import tensorflow as tf
import tf_utils as tfu
from graph.base import GraphPartBase
from tensorflow.python.ops.ragged.ragged_util import repeat


class Lemm(GraphPartBase):

    def __init__(self, for_usage, global_settings, current_settings, optimiser):
        super().__init__(for_usage, global_settings, current_settings, optimiser, 'lemm',["Loss","Accuracy","AccuracyByChar"])
        self.chars_count = self.chars_count + 1
        self.start_char_index = global_settings['start_token']
        self.end_char_index = global_settings['end_token']
        self.results = []
        self.results_lengths = []
        self.ys = []
        self.y_seq_lens = []
        self.cls = []
        self.keep_drops = []

    def __build_graph_for_device__(self, x, seq_len, batch_size, cls=None):
        self.xs.append(x)
        self.seq_lens.append(seq_len)

        if cls is None:
            cls = tf.placeholder(dtype=tf.int32, shape=(None,), name='XClass')

        if batch_size is None:
            batch_size = self.settings['batch_size']

        y = tf.placeholder(dtype=tf.int32, shape=(None, None), name='Y')
        y_seq_len = tf.placeholder(dtype=tf.int32, shape=(None,), name='YSeqLen')
        lemma_cls_init = tf.random_normal((self.main_classes_count, self.settings['encoder']['rnn_state_size']))
        lemma_cls_emb = tf.get_variable("EmbeddingsLemmaCls", initializer=lemma_cls_init)
        init_state = tf.nn.embedding_lookup(lemma_cls_emb, cls)
        start_tokens = tf.fill([batch_size], self.start_char_index)

        self.ys.append(y)
        self.y_seq_lens.append(y_seq_len)
        y_seq_len += 1

        with tf.variable_scope("encoder", reuse=tf.AUTO_REUSE):
            embedding_encoder = tf.get_variable(
                "embedding_encoder", [self.chars_count, self.settings['char_vector_size']])
#
        with tf.variable_scope("decoder", reuse=tf.AUTO_REUSE):
            embedding_decoder = tf.get_variable(
                "embedding_decoder", [self.chars_count, self.settings['char_vector_size']])

        encoder_input = tf.nn.embedding_lookup(embedding_encoder, x)

        decoder_output = tf.nn.embedding_lookup(embedding_decoder, x)


        #self.prints.append(tf.print("embeddings \n", embeddings))

        if self.for_usage:
            keep_drop = tf.constant(1, dtype=tf.float32, name='KeepDrop')
        else:
            keep_drop = tf.placeholder(dtype=tf.float32, name='KeepDrop')

        with tf.variable_scope('Encoder', reuse=tf.AUTO_REUSE) as scope:
            encoder_state, encoder_output = tfu.build_rnn(
                encoder_input,
                keep_drop,
                seq_len,
                self.settings['encoder'],
                init_state,
                init_state,
                self.for_usage,
                with_seq=True
            )

        with tf.variable_scope('Decoder', reuse=tf.AUTO_REUSE) as scope:

            if self.for_usage:

                #self.prints.append(tf.print("start_tokens \n", start_tokens))
                #helper = tf.contrib.seq2seq.SampleEmbeddingHelper(embeddings,
                #                                                  start_tokens=start_tokens,
                #                                                  end_token=self.end_char_index,
                #                                                  seed=1917)

                helper = tf.contrib.seq2seq.GreedyEmbeddingHelper(embedding_decoder,
                                                                  start_tokens=start_tokens,
                                                                  end_token=self.end_char_index)
            else:
                start_tokens_emd = tf.nn.embedding_lookup(embedding_decoder, start_tokens)
                #self.prints.append(tf.print("start_tokens emb\n", start_tokens_emd))
                start_tokens_emd = tf.reshape(start_tokens_emd, (batch_size, -1, self.settings['char_vector_size']))
                #self.prints.append(tf.print("encoder_output before\n", encoder_output))
                encoder_output = tf.concat(values=[start_tokens_emd, encoder_output], axis=1)
                #self.prints.append(tf.print("encoder_output after\n", encoder_output))

                end_tokens = tf.fill([batch_size], self.end_char_index)
                end_tokens_emd = tf.nn.embedding_lookup(embedding_decoder, end_tokens)
                end_tokens_emd = tf.reshape(end_tokens_emd, (batch_size, -1, self.settings['char_vector_size']))
                #self.prints.append(tf.print("lemma_output before\n", lemma_output))
                decoder_output = tf.concat([decoder_output, end_tokens_emd], axis=1)
                #self.prints.append(tf.print("lemma_output after\n", lemma_output))
                helper = tf.contrib.seq2seq.TrainingHelper(decoder_output,
                                                           [self.settings['max_length'] for _ in range(batch_size)],
                                                           time_major=False)
#
                end_tokens = tf.reshape(end_tokens, (batch_size, 1))
                y = tf.concat([y, end_tokens], axis=1)


            attention_mechanism = tf.contrib.seq2seq.BahdanauAttention(
               num_units=self.settings['encoder']['rnn_state_size'],
               memory=encoder_output,
               memory_sequence_length=seq_len
            )

            cell = tfu.rnn_cell(self.settings['decoder'],
                                self.for_usage)

            attn_cell = tf.contrib.seq2seq.AttentionWrapper(
               cell,
               attention_mechanism,
               attention_layer_size=self.settings['decoder']['rnn_state_size']/2
            )
            out_cell = tf.contrib.rnn.OutputProjectionWrapper(
                attn_cell,
                self.chars_count,
            )
            init_state = attn_cell.zero_state(dtype=tf.float32, batch_size=batch_size)#.clone(cell_state=encoder_state)
            decoder = tf.contrib.seq2seq.BasicDecoder(
                cell=out_cell,
                helper=helper,
                initial_state=init_state
            )
            outputs = tf.contrib.seq2seq.dynamic_decode(
                decoder=decoder,
                impute_finished=True,
                output_time_major=False,
                maximum_iterations=self.settings['max_length']
            )

            decoder_ids = outputs[0].sample_id
            decoder_logits = outputs[0].rnn_output
            decoder_length = outputs[2]

            #self.prints.append(tf.print("inputs \n", x))
            #self.prints.append(tf.print("results \n", decoder_ids))
            #self.prints.append(tf.print("lengths \n", decoder_length))

        masks = tf.sequence_mask(
            lengths=y_seq_len,
            dtype=tf.float32,
            maxlen=self.settings['max_length']
        )
        loss = tf.contrib.seq2seq.sequence_loss(
            decoder_logits,
            y,
            masks)
        vars = tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, scope=self.main_scope_name)
        grads = self.optimiser.compute_gradients(loss, var_list=vars)

        # loss accuracy
        metr_epoch_loss, metr_update, metr_reset = tfu.create_reset_metric(
            tf.metrics.mean,
            self.metric_names[0],
            loss
        )
        self.metrics_reset.append(metr_reset)
        self.metrics_update.append(metr_update)
        self.devices_metrics[self.metric_names[0]].append(metr_epoch_loss)

        # seq accuracy
        seq_mask = tf.cast(masks, tf.int32)
        #self.prints.append((tf.print("seq_mask", seq_mask)))
        self.prints.append(seq_mask)
        labels = y * seq_mask
        #self.prints.append((tf.print("labels", labels)))
        self.prints.append(labels)
        predictions = decoder_ids * seq_mask
        #self.prints.append((tf.print("predictions", predictions)))
        self.prints.append(predictions)
        delta = labels - predictions
        #self.prints.append((tf.print("delta", delta)))
        self.prints.append(delta)
        labels = tf.reduce_sum(delta * delta, 1)
        #self.prints.append((tf.print("labels", labels)))
        self.prints.append(labels)
        predictions = tf.zeros(batch_size)
        #self.prints.append((tf.print("rez predictions", predictions)))
        self.prints.append(predictions)
        metr_epoch_loss, metr_update, metr_reset = tfu.create_reset_metric(
            tf.metrics.accuracy,
            self.metric_names[1],
            labels=labels,
            predictions=predictions
        )
        self.metrics_reset.append(metr_reset)
        self.metrics_update.append(metr_update)
        self.devices_metrics[self.metric_names[1]].append(metr_epoch_loss)

        # char accuracy
        seq_mask = tf.cast(tf.reshape(masks, (-1,)), tf.int32)
        self.prints.append(seq_mask)
        nonzero_indices = tf.where(tf.not_equal(seq_mask, 0))
        self.prints.append(nonzero_indices)
        labels = tf.reshape(y, (-1,))
        labels = tf.gather(labels, nonzero_indices)
        labels = tf.reshape(labels, (-1,))
        #self.prints.append((tf.print("char labels", labels)))
        self.prints.append(labels)
        predictions = tf.reshape(decoder_ids, (-1,))
        predictions = tf.gather(predictions, nonzero_indices)
        predictions = tf.reshape(predictions, (-1,))
        #self.prints.append((tf.print("char predictions", predictions)))
        self.prints.append(predictions)
        metr_epoch_loss, metr_update, metr_reset = tfu.create_reset_metric(
            tf.metrics.accuracy,
            self.metric_names[2],
            labels=labels,
            predictions=predictions
        )
        self.metrics_reset.append(metr_reset)
        self.metrics_update.append(metr_update)
        self.devices_metrics[self.metric_names[2]].append(metr_epoch_loss)

        self.results.append(decoder_ids)
        self.results_lengths.append(decoder_length)
        self.cls.append(cls)
        self.dev_grads.append(grads)
        self.losses.append(loss)
        self.keep_drops.append(keep_drop)

    def __update_feed_dict__(self, op_name, feed_dict, batch, dev_num):
        feed_dict[self.cls[dev_num]] = batch['x_cls']
        feed_dict[self.ys[dev_num]] = batch['y']
        feed_dict[self.y_seq_lens[dev_num]] = batch['y_seq_len']
        feed_dict[self.keep_drops[dev_num]] = self.settings['keep_drop']

    def __load_dataset__(self, operation_name):
        return list(
            tfu.load_lemma_dataset(
                self.dataset_path,
                self.devices_count,
                operation_name,
                self.settings['batch_size']
            )
        )



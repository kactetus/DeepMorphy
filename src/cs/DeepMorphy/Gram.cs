using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Http.Headers;
using System.Runtime.InteropServices;
using System.Text;
using System.Xml;

namespace DeepMorphy
{
    class Gram
    {
        static Gram()
        {
            var enRuDic = new Dictionary<string, string>();
            var gramsDic = new Dictionary<string, Gram>();
            var gList = new List<Gram>();
            using (Stream stream = Utils.GetResourceStream("DeepMorphy.grams.xml"))
            {
                var rdr = XmlReader.Create(new StreamReader(stream, Encoding.UTF8));
                
                List<Cls> clsList = null;
                while (rdr.Read())
                {
                    
                    if (rdr.Name == "G" && rdr.NodeType == XmlNodeType.Element)
                    {
                        if (gList.Any())
                            gList.Last().Classes = clsList.ToArray();
                        
                        var gr = new Gram()
                        {
                            Index = int.Parse(rdr.GetAttribute("index")),
                            KeyEn = rdr.GetAttribute("key_en"),
                            KeyRu = rdr.GetAttribute("key_ru"),
                        };
                        enRuDic[gr.KeyEn] = gr.KeyRu;
                        
                        clsList = new List<Cls>();
                        gList.Add(gr);
                        gramsDic[gr.KeyEn] = gr;
                        gramsDic[gr.KeyRu] = gr;
                    }
                    else  if (rdr.Name == "C" && rdr.NodeType == XmlNodeType.Element)
                    {
                        var cls = new Gram.Cls()
                        {
                            NNIndex = rdr.GetAttribute("nn_index") == null
                                ? (long?) null
                                : long.Parse(rdr.GetAttribute("nn_index")),
                            KeyEn = rdr.GetAttribute("key_en"),
                            KeyRu = rdr.GetAttribute("key_ru"),
                        };
                        enRuDic[cls.KeyEn] = cls.KeyRu;
                        clsList.Add(cls);
                    }
                }
                gList.Last().Classes = clsList.ToArray();
            }

            Grams = gList.ToArray();
            EnRuDic = new ReadOnlyDictionary<string, string>(enRuDic);
            GramsDic = new ReadOnlyDictionary<string, Gram>(gramsDic);
        }



        
        
        public class Cls
        {
            public long? NNIndex { get; set; }
            public string KeyEn { get; set; }
            public string KeyRu { get; set; }
        }

        public int Index { get; private set; }
        public string KeyEn { get; private set; }
        public string KeyRu { get; private set; }
        public Cls[] Classes { get; private set; }

        private int? _nnClassesCount;
        public int NnClassesCount
        {
            get
            {
                if (!_nnClassesCount.HasValue)
                    _nnClassesCount = Classes.Count(x => x.NNIndex.HasValue);

                return _nnClassesCount.Value;
            }
        }

        private Dictionary<long, Cls> _nnDict;

        public Cls this[long i]
        {
            get
            {
                if (_nnDict == null)
                    _nnDict = Classes.Where(x => x.NNIndex.HasValue)
                                     .ToDictionary(x => x.NNIndex.Value, x => x);

                return _nnDict[i];
            }
        }
        

        public static Gram[] Grams { get; private set; }
        public static ReadOnlyDictionary<string, string> EnRuDic { get; private set; }
        public static ReadOnlyDictionary<string, Gram> GramsDic { get; private set; }

    }
}
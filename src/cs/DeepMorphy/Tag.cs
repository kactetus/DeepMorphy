using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;

namespace DeepMorphy
{
    /// <summary>
    /// Combination of grammemes for token
    /// </summary>
    public sealed class Tag
    {
        internal Tag(ReadOnlyDictionary<string, string> gramsDic, float power, string lemma=null, int? classIndex = null)
        {
            GramsDic = gramsDic;
            Power = power;
            ClassIndex = classIndex;
            Lemma = lemma;
        }
        
        internal int? ClassIndex { get; }
        
        /// <summary>
        /// Gram key -> Gram value dictionary
        /// </summary>
        public ReadOnlyDictionary<string, string> GramsDic { get; }

        /// <summary>
        /// Array of grammemes keys for current word
        /// </summary>
        public IEnumerable<string> Grams => GramsDic.Values;
        
        /// <summary>
        /// Probability for current combination
        /// </summary>
        public float Power { get; }
        
        /// <summary>
        /// Lemma for current combination
        /// </summary>
        public string Lemma { get; }
        
        /// <summary>
        /// Checks for grammemes in current tag
        /// </summary>
        /// <param name="grams">Grammemes to check</param>
        /// <returns>true if current tag contains all this grammemes else false</returns>
        public bool Has(params string[] grams)
        {
            return grams.All(gram => Grams.Contains(gram));
        }
        
        /// <summary>
        /// Returns grammeme for grammatical category
        /// </summary>
        /// <param name="gramCatKey">Grammatical category key</param>
        public string this[string gramCatKey]
        {
            get
            {
                if (GramsDic.ContainsKey(gramCatKey))
                    return GramsDic[gramCatKey];
                
                return null;
            }
        }

        public override string ToString()
        {
            var tags = string.Join(",", Grams);
            if (Lemma == null)
                return tags;
            else
                return $"Lemma: {Lemma} Tags: {tags}";
        }

    }
}
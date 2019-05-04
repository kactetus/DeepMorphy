using System;
using System.Collections.Generic;
using System.Dynamic;
using System.Linq;
using System.Security.Cryptography.X509Certificates;

namespace DeepMorphy.WordDict
{
    class Leaf
    {
        private bool _useEnTags;
        public Leaf(){}
        public Leaf(string text, bool useEnTags)
        {
            Text = text;
            _useEnTags = useEnTags;
        }
        public class LeafResult
        {
            public string[] Tags { get; set; }
        }
        private Dictionary<char, Leaf> _leaves = new Dictionary<char, Leaf>();
        private List<string[]> _results = new List<string[]>();
        
        public string Text { get; set; }
        public char Char { get; set; }
        public bool HasResults => _results.Count > 0;


        private Token _token;
        public Token Token
        {
            get
            {
                if (_token == null)
                {
                    var combs = _results.Select(x => 
                            new TagsCombination(x.Where(y => y != null).ToArray(), (float)1.0 / _results.Count)
                    ).ToArray();

                    var gDic = new Dictionary<string, TagCollection>();
                    foreach (var gram in Gram.Grams)
                    {
                        var gramName = _useEnTags ? gram.KeyEn : gram.KeyRu;
                        var tags = _results.Select(x => x[gram.Index])
                                           .Where(x => x != null)
                                           .ToArray();
                        if (tags.Length==0)
                            continue;
                        
                        var power = (float)1.0 / tags.Length;
                        gDic[gramName] = new TagCollection(tags.Select(x => new Tag(x, power)).ToArray());
                    }
                    _token = new Token(Text, combs, gDic);
                }
                return _token;
            }
        }

        public void AddLeaf(Leaf l)
        {
            _leaves[l.Char] = l;
        }

        public void AddResult(string[] lr)
        {
            _results.Add(lr);
        }

        public override string ToString()
        {
            return $"{Char} : {_leaves.Count}";
        }

        public Leaf this[char c]
        {
            get
            {
                if (!_leaves.ContainsKey(c))
                    return null;

                return _leaves[c];
            }
        }
    }
}
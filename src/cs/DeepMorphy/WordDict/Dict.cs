using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Xml;

namespace DeepMorphy.WordDict
{
    class Dict
    {
        private static readonly char[] CommmaSplitDict = new[] {','};
        private readonly Leaf _root;
        public Dict(bool useEnTags)
        {
            using (Stream stream = _getXmlStream())
            {
                var rdr = XmlReader.Create(new StreamReader(stream, Encoding.UTF8));
                _root = new Leaf(); 
                var leafStack = new Stack<Leaf>();
                while (rdr.Read())
                {
                    if (rdr.IsStartElement("L") )
                    {
                        var leaf = new Leaf(rdr.GetAttribute("t"), useEnTags);
                        leaf.Char = rdr.GetAttribute("c")[0];
                        if (leafStack.Count==0)
                            _root.AddLeaf(leaf);
                        else
                            leafStack.Peek().AddLeaf(leaf);
                        
                        leafStack.Push(leaf);
                    }
                    else if (rdr.IsStartElement("G") )
                    {
                        var leaf = leafStack.Peek();
                        var keys = rdr.GetAttribute("v").Split(CommmaSplitDict);
                        
                        if (!useEnTags)
                            keys = keys.Select(x => string.IsNullOrEmpty(x) ? null : Gram.EnRuDic[x])
                                .ToArray();
                        
                        leaf.AddResult(keys);
                    }
                    else if (rdr.Name == "L")
                    {
                        leafStack.Pop();
                    }
                }
            }
        }
        private Stream _getXmlStream()
        {
            var resourceName = $"DeepMorphy.WordDict.tree_dict.xml";
            return Utils.GetResourceStream(resourceName);
        }
        
        public Token Parse(string word)
        {
            return _parse(0, word, _root);
        }
        
        private Token _parse(int i, string word, Leaf leaf)
        {
            if (i == word.Length && leaf.HasResults)
                return leaf.Token;

            if (i == word.Length)
                return null;
            
            
            var nLeaf = leaf[word[i]];

            if (nLeaf == null)
                return null;

            return _parse(i + 1, word, nLeaf);

        }


    }
}
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;
using System.Xml;

namespace DeepMorphy.NeuralNet
{
    class Config
    {
        private readonly char[] _commmaSplitter = {','};

        public Config(bool useEnGrams, bool bigModel)
        {
            UseEnGrams = useEnGrams;
            BigModel = bigModel;
            _loadReleaseInfo();
        }
        
        public bool UseEnGrams { get; private set; }
        public bool BigModel { get; private set; }
        public int UndefinedCharId { get; private set; }
        public int StartCharIndex { get; private set; }
        public int EndCharIndex { get; private set; }
        
        public List<int> LemmaSameWordClasses { get; private set; } = new List<int>();
        public Dictionary<int, ReadOnlyDictionary<string, string>> ClsDic  { get; } = new Dictionary<int, ReadOnlyDictionary<string, string>>();
        public Dictionary<char, int> CharToId { get; private set; } = new Dictionary<char, int>();
        
        public Dictionary<int, char> IdToChar { get; private set; } = new Dictionary<int, char>();
        public Dictionary<string, string> OpDic { get; private set; } = new Dictionary<string, string>();
        public  Dictionary<string, string>  GramOpDic { get; private set; } = new Dictionary<string, string>();

        private void _loadReleaseInfo()
        {
            using (Stream stream = _getXmlStream(BigModel))
            {
                var rdr = XmlReader.Create(new StreamReader(stream, Encoding.UTF8));
                while (rdr.Read())
                {
                    if (rdr.Name == "Char" && rdr.NodeType == XmlNodeType.Element)
                    {
                        string val = rdr.GetAttribute("value");
                        int index = int.Parse(rdr.GetAttribute("index"));
                        if (val == "UNDEFINED")
                            UndefinedCharId = index;
                        else
                        {
                            CharToId[val[0]] = index;
                            IdToChar[index] = val[0];
                        }
                    }
                    else if (rdr.Name.Equals("G") && rdr.NodeType == XmlNodeType.Element)
                    {
                        var key = rdr.GetAttribute("key");
                        if (!UseEnGrams)
                            key = GramInfo.EnRuDic[key];

                        GramOpDic[key] = rdr.GetAttribute("op");
                    }
                    else if (rdr.Name.Equals("C") && rdr.NodeType == XmlNodeType.Element)
                    {
                        var index = int.Parse(rdr.GetAttribute("i"));
                        var keysStr = rdr.GetAttribute("v");
                        var keys = keysStr.Split(_commmaSplitter);
                        
                        if (!UseEnGrams)
                            keys = keys.Select(
                                x => string.IsNullOrWhiteSpace(x) ? x : GramInfo.EnRuDic[x]
                            ).ToArray();

                        var gramDic = keys.Select((val, i) => (gram: val, index: i))
                            .Where(tpl => !string.IsNullOrEmpty(tpl.gram))
                            .ToDictionary(
                                x => UseEnGrams 
                                    ? GramInfo.GramCatIndexDic[x.index].KeyEn 
                                    : GramInfo.GramCatIndexDic[x.index].KeyRu,
                                x => x.gram
                            );
                        
                        if (rdr.GetAttribute("lsw") != null)
                            LemmaSameWordClasses.Add(index);
                        
                        ClsDic[index] = new ReadOnlyDictionary<string, string>(gramDic);
                    }
                    else if (rdr.Name.Equals("Chars") && rdr.NodeType == XmlNodeType.Element)
                    {
                        StartCharIndex =  int.Parse(rdr.GetAttribute("start_char"));
                        EndCharIndex =  int.Parse(rdr.GetAttribute("end_char"));
                    }
                    else if (rdr.Name.Equals("Root") && rdr.NodeType == XmlNodeType.Element)
                    {
                        rdr.MoveToFirstAttribute();
                        OpDic[rdr.Name] = rdr.Value;
                        
                        while (rdr.MoveToNextAttribute())
                            OpDic[rdr.Name] = rdr.Value;
        
                        rdr.MoveToElement();
                    }
                }
            }
        }

        private Stream _getXmlStream(bool bigModel)
        {
            var modelKey = bigModel ? "big" : "small";
            var resourceName = $"DeepMorphy.NeuralNet.release_{modelKey}.xml";
            return Utils.GetResourceStream(resourceName);
        }


        public GramInfo this[string gramKey] => GramInfo.GramsDic[gramKey];

        public string this[string gramKey, long i]
        {
            get
            {
                var cls = GramInfo.GramsDic[gramKey][i];
                return UseEnGrams ? cls.KeyEn : cls.KeyRu;
            }
        }
    }
}
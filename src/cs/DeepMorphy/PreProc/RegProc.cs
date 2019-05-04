using System.Collections.Generic;
using System.Linq;
using System.Text.RegularExpressions;

namespace DeepMorphy.PreProc
{
    class RegProc : IPreProcessor
    {
        
        private static readonly Regex Reg;
        private static readonly string[] Groups;
        static RegProc()
        {
            var tpls = new[]
            {
                ("romn", @"(?=[MDCLXVI])M*(C[MD]|D?C*)(X[CL]|L?X*)(I[XV]|V?I*)"),
                ("int", @"[0-9]+"),
                ("punct", @"\p{P}+")
            };
            Groups = tpls.Select(x => x.Item1).ToArray();
            var groups =  tpls.Select(x=> $"(?<{x.Item1}>^{x.Item2}$)");

            var rezReg = string.Join("|", groups);
            rezReg = $"{rezReg}";
            Reg = new Regex(rezReg, RegexOptions.Compiled | RegexOptions.IgnoreCase);
        }

        private readonly char[] _availableChars;
        private int _minAvailablePersent;
        private bool _useEnTags;
        private Dictionary<string, Token> _tokensCache { get; set; } = new Dictionary<string, Token>();
        public RegProc(char[] availableChars, bool useEnTags, int minAvailablePersent)
        {
            _availableChars = availableChars;
            _minAvailablePersent = minAvailablePersent;
            _useEnTags = useEnTags;
        }
        
        public Token Parse(string word)
        {
            var match = Reg.Match(word);
            if (!match.Success)
            {
                var availableCount = word.Count(x => _availableChars.Contains(x));
                var availablePers = 100 * availableCount / word.Length;
                if (availablePers < _minAvailablePersent)
                    return GetPostToken(word, "unkn");
                return null;
            }

            foreach (var group in Groups)
            {
                var gr = match.Groups[group];
                if (gr.Success)
                    return GetPostToken(word, group);
            }

            return null;
        }
        
        private Token GetPostToken(string text, string tag)
        {
            if (_tokensCache.ContainsKey(tag))
            {
                var token = _tokensCache[tag];
                return token.MakeCopy(text);
            }
            else
            {
                var gram = "post";
                var tagKey = tag;
                if (!_useEnTags)
                {
                    tag = Gram.EnRuDic[tag];
                    gram = Gram.EnRuDic[gram];
                }

                var token = new Token(
                    text,
                    new []{new TagsCombination(new[]{tag}, (float)1.0)},
                    new Dictionary<string, TagCollection>()
                    {
                        {gram, new TagCollection(new[]{new Tag(tag, (float)1.0)})}
                    }
                );

                _tokensCache[tagKey] = token;
                return token;
            }
            
        }

    }
}
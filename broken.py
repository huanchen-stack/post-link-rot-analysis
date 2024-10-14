"""
Implementation of detection of broken pages from sic transit 
"""
from urllib.parse import urlparse, urljoin, urlunparse


from publicsuffixlist import PublicSuffixList
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qsl, parse_qs, urlsplit, urlunsplit, unquote
import re
import os, time
from bs4 import BeautifulSoup
from collections import defaultdict
import copy
import itertools
from dateutil import parser as dparser
import regex
import difflib
import datetime

from sklearn.feature_extraction.text import CountVectorizer
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer
from nltk.stem import WordNetLemmatizer


USER_AGENT = "Web Measure/1.0 (https://webresearch.eecs.umich.edu/overview-of-web-measurements/) Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"

PROXIES = {
    "http": f"http://52.160.40.241:8888",
    "https": f"http://52.160.40.241:8888"
}

def _safe_dparse(ts):
    try:
        return dparser.parse(ts)
    except:
        return datetime.datetime.now()

def filter_wayback(url):
    if 'web.archive.org/web' not in url:
        return url
    url = url.replace('http://web.archive.org/web/', '')
    url = url.replace('https://web.archive.org/web/', '')
    slash = url.find('/')
    url = url[slash + 1:]
    url = url.replace('http:/', 'http://')
    url = url.replace('http:///', 'http://')
    url = url.replace('https:/', 'https://')
    url = url.replace('https:///', 'https://')
    return url

def constr_wayback(url, ts):
    if 'web.archive.org/web' in url:
        return url
    return f"http://web.archive.org/web/{ts}/{url}"

def get_ts(wayback_url):
    if 'web.archive.org/web' not in wayback_url:
        return None
    wayback_url = wayback_url.replace('http://web.archive.org/web/', '')
    url = wayback_url.replace('https://web.archive.org/web/', '')
    slash = url.find('/')
    ts = url[:slash]
    return ts

def my_parse_qs(query):
    """Add case handler where the query string is not standard"""
    if not query:
        return {}
    pq = parse_qs(query)
    if len(pq) > 0:
        return pq
    else:
        return {'NoKey': [query]}

def normal_hostname(hostname):
    hostname = hostname.split(':')[0]
    hostname = hostname.split('.')
    if hostname[0] == 'www': hostname = hostname[1:]
    return '.'.join(hostname)

class HostExtractor:
    def __init__(self):
        self.psl = PublicSuffixList()
    
    def extract(self, url, wayback=False):
        """
        Wayback: Whether the url is got from wayback
        """
        if wayback:
            url = filter_wayback(url)
        if 'http://' not in url and 'https://' not in url:
            url = 'http://' + url
        hostname = urlsplit(url).netloc.strip('.').split(':')[0]
        return self.psl.privatesuffix(hostname)

class URLPatternDict:
    def __init__(self, max_diff=1):
        """max_diff: max number of tokens that can be different"""
        self.pattern_dict = defaultdict(list)
        self.max_diff = max_diff
        self.urls = set()
    
    def _detect_str_alnum(self, string):
            """Detect whether string has alpha and/or numeric char"""
            typee = ''
            alpha_char = [c for c in string if c.isalpha()]
            num_char = [c for c in string if c.isdigit()]
            if len(alpha_char) > 0:
                typee += 'A'
            if len(num_char) > 0:
                typee += 'N'
            return typee

    def _wildcard(self, pattern, idxs):
            """
            Do two things:
            1. Based on idx, change certain token in path/query into wildcard
            2. Specify wildcard type (Alpha/Numberic/AlphaNum/All)

            patterns: list of token
            idxs: tuple of idx, length depend on max_diff
            """
            seen = set()
            for idx in idxs:
                if idx in seen: continue
                seen.add(idx)
                if isinstance(pattern[idx], str):
                    # * Wildcard the path
                    str_type = self._detect_str_alnum(pattern[idx])
                    pattern[idx] = f'*{str_type}'
                else:
                    # * Wildcard the query
                    str_type = self._detect_str_alnum(pattern[idx][1])
                    token = list(pattern[idx])
                    token[1] = f'*{str_type}'
                    pattern[idx] = tuple(token)
            return pattern
    
    def _same_ext(self, url1, url2):
        path1 = urlsplit(url1).path
        path2 = urlsplit(url2).path
        return os.path.splitext(path1)[1] == os.path.splitext(path2)[1]

    def gen_patterns(self, url):
        us = urlsplit(url)
        us = us._replace(netloc=us.netloc.split(':')[0])
        site = he.extract(url)
        host = normal_hostname(us.netloc)
        host_list = host.replace(site, '').strip('.').split('.')
        if us.path == '':
            us = us._replace(path='/')
        if us.path[-1] == '/' and us.path != '/':
            us = us._replace(path=us.path[:-1])
        host_list = list(filter(lambda x: x!= '', host_list))
        path_list = list(filter(lambda x: x!= '', us.path.split('/')))
        query_list = {k: v[0] for k, v in my_parse_qs(us.query).items()}
        query_list = sorted(query_list.items())
        # ! TEMP COMMENTED
        # pattern_list = host_list + path_list + query_list
        pattern_list = path_list + query_list
        patterns = []
        total = len(pattern_list)
        idxs_combination = list(itertools.combinations_with_replacement(range(total), self.max_diff))
        # * Reorder combination so that lower diff comes first
        idxs_combination.sort(key=lambda x: len(set(x)))
        for idxs in idxs_combination:
            new_pattern = copy.deepcopy(pattern_list)
            new_pattern = self._wildcard(new_pattern, idxs)
            # ! TEMP ADDED
            new_pattern.insert(0, host)
            patterns.append(tuple(new_pattern))
        return patterns

    def add_url(self, url):
        if url in self.urls:
            return
        self.urls.add(url)
        patterns = self.gen_patterns(url)
        for pat in patterns:
            self.pattern_dict[pat].append(url)
    
    def match_url(self, url, least_match=2, match_ext=False):
        """
        Note: A URL may appear in multiple objs due to different match reasons
        match_ext: whether ext needs to be matched
        Return: [{
            "urls": [matched urls],
            "pattern": matched pattern
        }]
        """
        patterns = self.gen_patterns(url)
        seen_match = set()
        matched = []
        for pat in patterns:
            if pat in self.pattern_dict:
                matched_urls = self.pattern_dict[pat]
                if len(matched_urls) < least_match:
                    continue
                if tuple(sorted(matched_urls)) in seen_match:
                    continue
                if match_ext:
                    matched_urls = [u for u in matched_urls if self._same_ext(u, url)]
                seen_match.add(tuple(sorted(matched_urls)))
                matched.append({
                    "urls": matched_urls,
                    "pattern": pat
                })
        return matched
    
    def match_pattern(self, pattern):
        return self.pattern_dict.get(pattern, [])

    def pop_matches(self, least_match=2):
        """Pop all matched URL pattern in the dict"""
        seen_match = set()
        matched = []
        for pat, urls in self.pattern_dict.items():
            if len(urls) < least_match:
                continue
            if tuple(sorted(urls)) in seen_match:
                continue
            seen_match.add(tuple(sorted(urls)))
            matched.append({
                'urls': urls,
                'pattern': pat
            })
        return matched

he = HostExtractor()


def get_num_words(string):
    filter_str = ['', '\n', ' ']
    string_list = string.split()
    string_list = list(filter(lambda x: x not in filter_str, string_list))
    return ' '.join(string_list)


def find_link_density(html):
    """
    Find link density of a webpage given html
    """
    try:
        soup = BeautifulSoup(html, 'lxml')
    except:
        return 0
    filter_tags = ['style', 'script']
    for tag in filter_tags:
        for element in soup.findAll(tag):
            element.decompose()
    total_text = get_num_words(soup.get_text(separator=' '))
    total_length = len(total_text)
    atag_length = 0
    for atag in soup.findAll('a'):
        atag_text = get_num_words(atag.get_text())
        atag_length += len(atag_text)
    return atag_length / total_length if total_length != 0 else 0


def status_categories(status):
    """
    Given a detailed status code (or possibly its detail)
    Return a better categorized status
    Consider status = list of string as Soft-404
    Soft-404/ 4/5xx / DNSErrorOtherError
    """
    # if not re.compile("^([2345]|DNSError|OtherError)").match(status): return "Unknown"
    status = f'{status}' # Put status into string
    if re.compile("^[45]").match(status): return "4/5xx"
    elif re.compile("^(DNSError|OtherError)").match(status): return "DNSOther"
    elif re.compile("^(\[.*\]|Similar|Same|no features)").match(status): return "Soft-404"
    else:
        return status


def url_match(url1, url2, wayback=True, case=False):
    """
    Compare whether two urls are identical on filepath and query
    If wayback is set to True, will first try to filter out wayback's prefix

    case: whether token comparison is token sensitive
    """
    if wayback:
        url1 = filter_wayback(url1)
        url2 = filter_wayback(url2)
    up1, up2 = urlparse(url1), urlparse(url2)
    netloc1, path1, query1 = up1.netloc.split(':')[0], up1.path, up1.query
    netloc2, path2, query2 = up2.netloc.split(':')[0], up2.path, up2.query
    if not case:
        netloc1, path1, query1 = netloc1.lower(), path1.lower(), query1.lower()
        netloc2, path2, query2 = netloc2.lower(), path2.lower(), query2.lower()
    netloc1, netloc2 = netloc1.split('.'), netloc2.split('.')
    if netloc1[0] == 'www': netloc1 = netloc1[1:]
    if netloc2[0] == 'www': netloc2 = netloc2[1:]
    if '.'.join(netloc1) != '.'.join(netloc2):
        return False
    if path1 == '': path1 = '/'
    if path2 == '': path2 = '/'
    if path1 != '/' and path1[-1] == '/': path1 = path1[:-1]
    if path2 != '/' and path2[-1] == '/': path2 = path2[:-1]
    dir1, file1 = os.path.split(path1)
    dir2, file2 = os.path.split(path2)
    if re.compile('^index').match(file1): path1 = dir1
    if re.compile('^index').match(file2): path2 = dir2
    if path1 != path2:
        return False
    if query1 == query2:
        return True
    qsl1, qsl2 = sorted(parse_qsl(query1), key=lambda kv: (kv[0], kv[1])), sorted(parse_qsl(query2), key=lambda kv: (kv[0], kv[1]))
    return len(qsl1) > 0 and qsl1 == qsl2


def url_norm(url, wayback=False, case=False, ignore_scheme=False, trim_www=False,\
                trim_slash=False, sort_query=True):
    """
    Perform URL normalization
    common: Eliminate port number, fragment
    ignore_scheme: Normalize between http and https
    trim_slash: For non homepage path ending with slash, trim if off
    trim_www: For hostname start with www, trim if off
    sort_query: Sort query by keys
    """
    if wayback:
        url = filter_wayback(url)
    us = urlsplit(url)
    netloc, path, query = us.netloc, us.path, us.query
    netloc = netloc.split(':')[0]
    if ignore_scheme:
        us = us._replace(scheme='http')
    if trim_www and netloc.split('.')[0] == 'www':
        netloc = '.'.join(netloc.split('.')[1:])
    us = us._replace(netloc=netloc, fragment='')
    if not case:
        path, query = path.lower(), query.lower()
    if path == '': 
        us = us._replace(path='/')
    elif trim_slash and path[-1] == '/':
        us = us._replace(path=path[:-1])
    if query and sort_query:
        qsl = sorted(parse_qsl(query), key=lambda kv: (kv[0], kv[1]))
        if len(qsl):
            us = us._replace(query='&'.join([f'{kv[0]}={kv[1]}' for kv in qsl]))
    return urlunsplit(us)


def url_parent(url, exclude_digit=False):
    """
    exclude_digit: When considering the parent. full digit tokens are filtered out
        This is used because full digit token are usually id, which are likely to be unique
    Return parent of url
    """
    us = urlsplit(url)
    site = he.extract(url)
    if us.path in ['', '/'] and not us.query:
        if site == us.netloc.split(':')[0]: return url
        hs = us.netloc.split(':')[0].split('.')
        return urlunsplit(us._replace(netloc='.'.join(hs[1:])))
    path = us.path
    if path and path [-1] == '/' and not us.query: path = path[:-1]
    if not exclude_digit:
        path = os.path.dirname(path)
    else:
        path = nondigit_dirname(path)
    return urlunsplit(us._replace(path=path, query=''))

def nondigit_dirname(path):
    """
    Return closest parent of URL where there is no digit token
    """
    if path not in ['', '/'] and path[-1] == '/':
        path = path[:-1]
    parts = path.split('/')
    parts = parts[:-1]
    while len(parts) and parts[-1].isdigit():
        parts = parts[:-1]
    return '/'.join(parts)

def nondate_pathname(path):
    """
    For every token in the path, filter out dates (keep the remaining parts)
    """
    if path not in ['', '/'] and path[-1] == '/':
        path = path[:-1]
    parts = path.split('/')
    new_parts = []
    for p in parts:
        try:
            _, remaining = dparser.parse(p, fuzzy_with_tokens=True)
            if len(remaining) == 0:
                new_p = '${date}'
            elif len(remaining) == 1:
                new_p = remaining[0] + '${date}'
            else:
                new_p = '${date}'.join(remaining)
        except:
            new_p = p
        new_parts.append(new_p)
    return '/'.join(new_parts)
    

def is_parent(parent, url):
    """
    Check whether parent is truely a parent of url
    filename with ^index is considered as /

    Return Boolean
    """
    us, ps = urlsplit(url), urlsplit(parent)
    h1s, h2s = us.netloc.split(':')[0].split('.'), ps.netloc.split(':')[0].split('.')
    if h1s[0] == 'www': h1s = h1s[1:]
    if h2s[0] == 'www': h2s = h2s[1:]
    for h1, h2 in zip(reversed(h1s), reversed(h2s)):
        if h1 != h2: return False
    p1s, p2s = us.path, ps.path
    if p1s == '': p1s = '/'
    if p2s == '': p2s = '/'
    if p1s != '/' and p1s[-1] == '/': p1s = p1s[:-1]
    if p2s != '/' and p2s[-1] == '/': p2s = p2s[:-1]
    if len(h2s) != len(h1s):
        if len(h1s) - len(h2s) not in [0, 1] or p1s != p2s or us.query != ps.query:
            return False
    p1s, p2s = p1s.split('/')[1:], p2s.split('/')[1:]
    if re.compile('^index').match(p2s[-1]):
        p2s = p2s[:-1]
    for p1, p2 in zip(p1s, p2s):
        if p1 != p2: return False
    if len(p1s) - len(p2s) != 1:
        return False
    q1s, q2s = set(parse_qsl(us.query)), set(parse_qsl(ps.query))
    if len(q1s) == 0 and us.query or (len(q2s) == 0 and ps.query):
        return us.query == ps.query
    for q2 in q2s:
        if q2 not in q1s: return False
    return True


def is_prefix(prf, url):
    """
    Check whether ans is the prefix of url (prefix including indentical URLs)
    filename with ^index is considered as /

    Return Boolean
    """
    us, ps = urlsplit(url), urlsplit(prf)
    h1s, h2s = us.netloc.split(':')[0].split('.'), ps.netloc.split(':')[0].split('.')
    if h1s[0] == 'www': h1s = h1s[1:]
    if h2s[0] == 'www': h2s = h2s[1:]
    for h1, h2 in zip(reversed(h1s), reversed(h2s)):
        if h1 != h2: return False
    p1s, p2s = us.path, ps.path
    if p1s == '': p1s = '/'
    if p2s == '': p2s = '/'
    if p1s != '/' and p1s[-1] == '/': p1s = p1s[:-1]
    if p2s != '/' and p2s[-1] == '/': p2s = p2s[:-1]
    if len(h2s) != len(h1s):
        if len(h1s) - len(h2s) not in [0, 1] or p1s != p2s or us.query != ps.query:
            return False
    p1s, p2s = p1s.split('/')[1:], p2s.split('/')[1:]
    if re.compile('^index').match(p2s[-1]):
        p2s = p2s[:-1]
    for p1, p2 in zip(p1s, p2s):
        if p1 != p2: return False
    if len(p1s) - len(p2s) < 0:
        return False
    q1s, q2s = set(parse_qsl(us.query)), set(parse_qsl(ps.query))
    if len(q1s) == 0 and us.query or (len(q2s) == 0 and ps.query):
        return us.query == ps.query
    for q2 in q2s:
        if q2 not in q1s: return False
    return True


def path_edit_distance(url1, url2):
    us1, us2 = urlsplit(url1), urlsplit(url2)
    dis = 0
    h1s, h2s = us1.netloc.split(':')[0].split('.'), us2.netloc.split(':')[0].split('.')
    if h1s[0] == 'www': h1s = h1s[1:]
    if h2s[0] == 'www': h2s = h2s[1:]
    if h1s != h2s:
        dis += 1
    path1 = list(filter(lambda x: x!= '', us1.path.split('/')))
    path2 = list(filter(lambda x: x!= '', us2.path.split('/')))
    for part1, part2 in zip(path1, path2):
        if part1 != part2: dis += 1
    dis += abs(len(path1) - len(path2))
    query1, query2 = sorted(parse_qsl(us1.query)), sorted(parse_qsl(us2.query))
    dis += (query1 != query2)
    return dis


def tree_diff(dest, src):
    seq1, seq2 = [], []
    us1, us2 = urlsplit(dest), urlsplit(src)
    h1s, h2s = us1.netloc.split(':')[0], us2.netloc.split(':')[0]
    seq1.append(h1s)
    seq2.append(h2s)
    p1s, p2s = us1.path, us2.path
    if p1s == '': p1s == '/'
    if p2s == '': p2s == '/'
    p1s, p2s = p1s.split('/'), p2s.split('/')
    seq1 += p1s[1:]
    seq2 += p2s[1:]
    diff = 0
    for i, (s1, s2) in enumerate(zip(seq1, seq2)):
        if s1 != s2: 
            diff += 1
            break
    diff += len(seq1) + len(seq2) - 2*(i+1)
    q1s, q2s = parse_qsl(us1.query), parse_qsl(us2.query)
    if diff == 0:
        diff += len(set(q1s).union(q2s)) - len(set(q1s).intersection(q2s))
    else:
        diff += min(len(q1s), len(set(q1s).union(q2s)) - len(set(q1s).intersection(q2s)))
    return diff


def common_prefix_diff(dest, src):
    """Distance from dest to common path prefix"""
    us1 = urlsplit(dest)
    us2 = urlsplit(src)
    p1s, p2s = us1.path, us2.path
    if p1s == '': p1s == '/'
    if p2s == '': p2s == '/'
    if len(p1s) > 1 and p1s[-1] == '/': p1s = p1s[:-1]
    if len(p2s) > 1 and p2s[-1] == '/': p2s = p2s[:-1]
    p1s, p2s = p1s.split('/')[1:], p2s.split('/')[1:]
    if us1.netloc.split(':')[0] != us2.netloc.split(':')[0]:
        return len(p1s) - 1
    i = 0
    for i, (s1, s2) in enumerate(zip(p1s, p2s)):
        if s1 != s2:
            i -= 1
            break
    i += 1
    return len(p1s) - i if i < len(p1s) else i - len(p2s)


def netloc_dir(url, nondigit=True, nondate=False, exclude_index=False):
    """
    Get host, nondigit_dirname for a URL
    nondigit: whether to perform nondigit dirname processing
    nondate: whether to perform nondate pathname processing
    exclude_index: If set True, any filename with index (e.g. index.php)
                    will be considered directory with 1 more level up
    """
    url = filter_wayback(url)
    us = urlsplit(url)
    p = us.path
    if len(p) > 1 and p[-1] == '/': p = p[:-1]
    if p == '':  p == '/'
    if exclude_index:
        p = p.split('/')
        filename = os.path.splitext(p[-1])[0]
        if 'index' == filename or 'default' == filename:
            p = p[:-1]
        p = '/'.join(p)
    hosts = us.netloc.split(':')[0].split('.')
    if 'www' in hosts[0]: hosts = hosts[1:]
    if nondigit:
        p = nondigit_dirname(p)
    if nondate:
        p = nondate_pathname(p)
    return ('.'.join(hosts), p.lower())

stemmer = None 
lemmatizer = None
stem_cache = {}

def tokenize(texts, stop_words='english', stemming=True):
    """
    Simple function for tokenizing a text. Extracted from sklearn src code
    
    Returns: list of features in the original order
    """
    global stemmer, lemmatizer, stem_cache
    if stemmer is None:
        stemmer = SnowballStemmer('english')
        lemmatizer = WordNetLemmatizer()
    texts = texts.replace('_', ' ')
    # # ? Tokenize: Scikit-Learn version
    cv = CountVectorizer(stop_words=stop_words, token_pattern=r"(?u)\b\w+\b") # TODO: Not necessary english
    analyze = cv.build_analyzer()
    texts = analyze(texts)
    # ? Tokenize: nltk version
    # texts = nltk.word_tokenize(texts)
    def cached_transform(t, func, cache):
        if t in cache:
            return cache[t]
        tt = func(t)
        cache[t] = tt
        return tt
    # * Stemming
    if stemming:
        texts = [cached_transform(t, stemmer.stem, stem_cache) for t in texts]
    # * Lemmatization
    # texts = [lemmatizer.lemmatize(t) for t in texts]
    return texts

def tokenize_url(url, include_all=False, process=False):
    """
    include_all: if host & query will be included in the tokens
    process: Whether each token of URL will be further tokenized (like text tokenize)
                if set True, all tokens will be tokenized
                if set as file, only filename will be tokenized 
    """
    us = urlsplit(url)
    path = unquote(us.path.lower())
    query = unquote(us.query.lower())
    qsl = sorted(parse_qsl(query))
    if path == '': path = '/'
    if path[-1] == '/' and path != '/': path = path[:-1]
    path = path.split('/')[1:]
    tokens = []
    if include_all:
        host = unquote(us.netloc.split(':')[0].lower())
        host = host.split('.')
        if host[0] == 'www': host = host[1:]
        tokens.append('.'.join(host))
    for i, p in enumerate(path):
        token = unquote(p)
        if process == True or (process == 'file' and i == len(path)-1):
            token = os.path.splitext(token)[0]
            token = tokenize(token, stop_words=[])
            token = ' '.join(token)
        tokens.append(token.lower())
    for k, v in qsl:
        tokens.append(f"{v.lower()}")
    return tokens

def url_token_diffs(url1_tokens, url2_tokens):
    """
    return: [(index, operation(C:change,A:add,D:delete), text)]
    """
    tokendiffs = []
    diffs = [d for d in difflib.ndiff(url1_tokens, url2_tokens) if d[0] != '?']
    # print(diffs)
    i = 0
    counter = 0
    stack = []
    def _difflib2mydiff(i, d):
        nonlocal counter
        t = {'+': 'A', '-': 'D'}
        r = (i, t[d[0]], d[2:])
        if d[0] == '-': counter += 1
        return r
    while i < len(diffs):
        diff = diffs[i]
        if diff[0] == ' ': # * No Change, pop stack
            for j, d in stack: tokendiffs.append(_difflib2mydiff(j, d))
            stack = []
            counter += 1
        elif diff[0] == '+': # * Pop stack if stack is -
            if len(stack) and stack[0][1][0] == '-':
                j, d = stack.pop(0)
                tokendiffs.append((j, 'C', diff[2:]))
            else:
                stack.append((counter, diff))
        elif diff[0] == '-': # * Pop stack if stack is +
            if len(stack) and stack[0][1][0] == '+':
                j, d = stack.pop(0)
                tokendiffs.append((counter, 'C', d[2:]))
            else:
                stack.append((counter, diff))
            counter += 1
        else:
            raise
        i += 1
    for j, d in stack: tokendiffs.append(_difflib2mydiff(counter, d))
    if len(tokendiffs) > 0 and tokendiffs[0][0] == 0: # * Hostname change, should be aligned
        tokendiffs[0] = (0, f'C {tokendiffs[0][2]}', tokendiffs[0][2])
    return tokendiffs

def order_diffs(diffs):
    """
    diffs: [delta]
    1. Based on delta length
    2. Based on delta starting changing point
    """
    diff_length = defaultdict(set)
    for diff in diffs:
        length = len(diff)
        diff_length[length].add(diff)
    return [d[1] for d in sorted(diff_length.items())]

def url_alias_diff(url, alias, process='file'):
    url_tokens = tokenize_url(url, include_all=True, process=process)
    alias_tokens = tokenize_url(alias, include_all=True, process=process)
    example_diffs = url_token_diffs(url_tokens, alias_tokens)
    return tuple(sorted(e[:2] for e in example_diffs))

def url_alias_filename_simi(url, alias):
    url_file = urlsplit(url).path
    url_file = os.path.basename(url_file)
    url_file, _ = os.path.splitext(url_file)
    alias_file = urlsplit(alias).path
    alias_file = os.path.basename(alias_file)
    alias_file, _ = os.path.splitext(alias_file)
    url_file_tokens = regex.split("[^a-zA-Z1-9]", url_file.lower())
    url_file_tokens = list(filter(lambda x: x!="", url_file_tokens))
    alias_file_tokens = regex.split("[^a-zA-Z1-9]", alias_file.lower())
    alias_file_tokens = list(filter(lambda x: x!="", alias_file_tokens))
    itst = set(url_file_tokens).intersection(alias_file_tokens)
    union = set(url_file_tokens).union(alias_file_tokens)
    if len(union) == 0: return 0
    return len(itst)/len(union)

def url_title_simi(url, title):
    """
    Calculate the overlapping tokens between title and url (currently filename)
    """
    path = urlsplit(url).path
    if path not in ['', '/'] and path[-1] == '/': path = path[:-1]
    filename = os.path.basename(path)
    filename, _ = os.path.splitext(filename)
    url_tokens = regex.split("[^a-zA-Z1-9]", filename.lower())
    title_tokens = regex.split("[^a-zA-Z1-9]", title.lower())
    url_tokens = list(filter(lambda x: x!="", url_tokens))
    if len(url_tokens) == 0:
        return 0
    title_tokens = list(filter(lambda x: x!="", title_tokens))
    diffs = list(difflib.ndiff(url_tokens, title_tokens))
    overlap = [d[2:] for d in diffs if d[0] == ' ']
    # print(overlap, url_tokens)
    return len(overlap) / len(url_tokens)

def order_neighbors(target_url, neighbors, urlgetter=None,
                    ts=None, prefix_funcs=[], suffix_funcs=[],
                    middle_funcs=[]):
    """
    Order neighbors so that most similar neighbor will be ranked first
    urlgetter: lambda to get url from neighbors
    ts: str/datetime. If set, neighbors url needs to be in the wayback form
    prefix/suffix_funcs: self defined function that generate first/last scores for the ranking
    middle_func: [(func, insert_idx)]

    return: Sorted neighbors
    """
    if urlgetter is None:
        urlgetter = lambda x: x
    def get_ext(url):
        path = urlsplit(url).path
        if path not in ['/', ''] and path[-1] == '/': path = path[:-1]
        return os.path.splitext(path)[1]
    def query_score(url):
        scores = []
        target_query = urlsplit(target_url).query
        query = urlsplit(url).query
        # * Has query?
        scores.append(-((target_query != "") == (query != "")))
        target_qs = parse_qs(target_query)
        qs = parse_qs(query)
        # * How many same keys?
        same_keys = set(target_qs.keys()).intersection(qs.keys())
        scores.append(-len(same_keys))
        # * How many same values
        same_values = 0
        for k in same_keys:
            same_values += len(set(target_qs[k]).intersection(qs[k]))
        scores.append(-same_values)
        return tuple(scores)
    def _detect_file_alnum(url):
        """Detect whether string has alpha and/or numeric char"""
        path = urlsplit(url).path
        if path not in ['/', ''] and path[-1] == '/': path = path[:-1]
        filename = os.path.basename(path)
        typee = ''
        alpha_char = [c for c in filename if c.isalpha()]
        num_char = [c for c in filename if c.isdigit()]
        if len(alpha_char) > 0:
            typee += 'A'
        if len(num_char) > 0:
            typee += 'N'
        return set(typee)
    lambdas = prefix_funcs.copy()
    # * Same ext?
    lambdas.append(lambda x: -(get_ext(target_url) == get_ext(x)) )
    # * Format similarity
    lambdas.append(lambda x: -len(set(tokenize_url(target_url)).intersection(tokenize_url(x))))
    lambdas.append(lambda x: -len(_detect_file_alnum(target_url).intersection(_detect_file_alnum(x))))
    # * Has query? Same Key? Same Value?
    lambdas.append(lambda x: query_score(x))
    if ts:
        if isinstance(ts, str):
            ts = _safe_dparse(ts)
        # * ts diff
        lambdas.append(lambda x: abs((_safe_dparse(get_ts(x)) - ts).total_seconds()))
    lambdas += suffix_funcs.copy()
    neighbor_score = []
    for neighbor in neighbors:
        score = tuple(l(urlgetter(neighbor)) for l in lambdas)
        neighbor_score.append((neighbor, score))
    neighbor_score.sort(key=lambda x: x[1])
    return [r[0] for r in neighbor_score]


def na_url(url):
    """Check whether the URL (either broken or alias) is n/a for study (including unwanted keywords)"""
    keywords = ['login', 'subscription', 'error', 'notfound', '404', 'badpage', 'errorpath']
    path = urlsplit(url).path
    if path not in ["/", ""] and path[-1] == "/": path = path[:-1]
    filename = path.split("/")[-1]
    filename = set(tokenize(filename, stop_words=[], stemming=False))
    for k in keywords:
        if k in filename:
            return True
    return False

def suspicious_alias(url, alias):
    if na_url(alias):
        return True
    alias_us = urlsplit(alias)
    is_home = lambda u: urlsplit(u).path in ['', '/']
    # * Non home to home page
    if not is_home(url) and is_home(alias):
        return True
    # * Non HTML
    _, ext = os.path.splitext(alias_us.path)
    if ext.lower() in {'.pdf', '.jpeg', '.jpg', '.doc'}:
        return True
    return False

def path_common_prefix(urls):
    """Get path common prefix of URLs"""
    paths = []
    for url in urls:
        path = urlsplit(url).path
        paths.append(path)
    return os.path.commonpath(paths)


from lib2to3.pgen2 import token
import requests
from urllib.request import urlopen, Request, ProxyHandler, build_opener, install_opener
import re
import os
from urllib.parse import urlparse, parse_qsl, urlsplit, urlunsplit
import random, string
import sys
from math import ceil
from bs4 import BeautifulSoup


import logging
logger = logging.getLogger('logger')

def get_canonical(url, html):
    """See whether there are canonical tag in the HTML. If no, return the original URL"""
    try:
        soup = BeautifulSoup(html, 'lxml')
    except:
        return url
    base = soup.find('base')
    base_url = url if base is None else urljoin(url, base.get('href'))
    cans = soup.find_all('link', {'rel': 'canonical'})
    can = ''
    if len(cans) > 0:
        # ! Why is urlsplit(url).path not in ['', '/'] previously useful?
        if cans[0].get('href'):
            can = cans[0]['href']
            return urljoin(base_url, can) 
    return url

from os.path import join, dirname, abspath, splitext
from subprocess import call
import re, os, time
import sys, copy
import multiprocessing as mp
from multiprocessing import Process
import scipy.sparse as sp
import numpy as np
from collections import defaultdict
import functools
from subprocess import Popen, PIPE
import requests

from langcodes import Language
from langdetect import detect_langs

# import justext
from goose3 import Goose
# from newspaper import Article

import textwrap
from dateutil import parser as dparser
from dateparser.search import search_dates
import dateparser, difflib

import brotli
import bs4
from bs4 import BeautifulSoup

from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer
from nltk.stem import WordNetLemmatizer


stemmer = SnowballStemmer('english')
lemmatizer = WordNetLemmatizer()

stem_cache = {}
def tokenize(texts):
    """
    Simple function for tokenizing a text. Extracted from sklearn src code
    
    Returns: list of features in the original order
    """
    texts = texts.replace('_', ' ')
    # # ? Tokenize: Scikit-Learn version
    cv = CountVectorizer(stop_words='english', token_pattern=r"(?u)\b\w+\b") # TODO: Not necessary english
    analyze = cv.build_analyzer()
    texts = analyze(texts)
    # ? Tokenize: nltk version
    # texts = nltk.word_tokenize(texts)
    def cached_transform(t, func, cache):
        if t in cache:
            return cache[t]
        tt = func(t)
        cache[t] = tt
        return tt
    # * Stemming
    texts = [cached_transform(t, stemmer.stem, stem_cache) for t in texts]
    # * Lemmatization
    # texts = [lemmatizer.lemmatize(t) for t in texts]
    return texts

def k_shingling(text1, text2, k=5):
    text1 = tokenize(text1)
    text2 = tokenize(text2)
    if len(text1) < k:
        shingle1 = [tuple(text1)]
    else:
        shingle1 = [tuple(text1[i: i+k]) for i in range(len(text1)-(k-1))]
    if len(text2) < k:
        shingle2 = [tuple(text2)]
    else:
        shingle2 = [tuple(text2[i: i+k]) for i in range(len(text2)-(k-1))]
    if len(shingle1) + len(shingle2) <= 0: return 1
    return len(set(shingle1).intersection(set(shingle2))) / len(set(shingle1).union(set(shingle2)))



sys.setrecursionlimit(1500)
he = HostExtractor()


proxy_handler = ProxyHandler(PROXIES)
opener = build_opener(proxy_handler)
install_opener(opener)

def alternative_request(url, timeout=15):
    global USER_AGENT
    httprequest = Request(url, headers={"user-agent": USER_AGENT})
    with urlopen(httprequest, timeout=timeout) as response:
        r = requests.Response()
        r.status_code = response.status
        if isinstance(response.url, bytes):
            r.url = response.url.decode('utf-8')
        else:
            r.url = response.url
        r.headers = dict(response.headers)
        r._content = response.read()
        return r

# rp = RobotParser()

def send_request(url, timeout=15):
    """Only fetch for response body when content-type is HTML"""
    resp = None
    global USER_AGENT
    requests_header = {'user-agent': USER_AGENT}

    req_failed = True
    # if not rp.allowed(url, requests_header['user-agent']):
    #     return None, 'Not Allowed'
    try:
        global PROXIES
        resp = requests.get(url, headers=requests_header, timeout=timeout, stream=True, proxies=PROXIES, verify=False)
        # resp = requests.get(url, headers=requests_header, timeout=timeout, stream=True, verify=False)
        headers = {k.lower(): v.lower() for k, v in resp.headers.items()}
        content_type = headers['content-type'] if 'content-type' in headers else ''
        if 'html' in content_type:
            content = resp.content
        req_failed = False
    # Requsts timeout
    except requests.exceptions.ReadTimeout:
        error_msg = 'ReadTimeout'
    except requests.exceptions.Timeout:
        error_msg = 'Timeout'
    # DNS Error or tls certificate verify failed
    except requests.exceptions.ConnectionError as exc:
        reason = str(exc)
        # after looking for the failure info, the following should be the errno for DNS errors.
        if ("[Errno 11001] getaddrinfo failed" in reason or     # Windows
            "[Errno -2] Name or service not known" in reason or # Linux
            "[Errno 8] nodename nor servname " in reason):      # OS X
            error_msg = 'ConnectionError_DNSLookupError'
        else:
            error_msg = 'ConnectionError'
    except requests.exceptions.MissingSchema:
        error_msg = 'MissingSchema'
    except requests.exceptions.InvalidSchema:
        error_msg = 'InvalidSchema'
    except requests.exceptions.TooManyRedirects:
        try:
            resp = alternative_request(url)
            req_failed = False
        except:
            error_msg = 'TooManyRedirects'
    except requests.exceptions.RequestException:
        error_msg = 'RequestException'
    except UnicodeError:
        error_msg = 'ERROR_UNICODE'
    except Exception as _:
        error_msg = 'ERROR_REQUEST_EXCEPTION_OCCURRED'

    if req_failed:
        return resp, error_msg

    return resp, 'SUCCESSFUL'


def get_status(url, resp, msg):
    status, detail = "", ""
    if msg == 'SUCCESSFUL':
        final_url, status_code = resp.url, resp.status_code
        url_path = urlparse(url).path
        final_url_path = urlparse(final_url).path
        # remove the last '/' if it exists
        if url_path.endswith('/'):
            url_path = url_path[:-1]
        if final_url_path.endswith('/'):
            final_url_path = final_url_path[:-1]
        
        status = str(status_code)
        # if the response status code is 400 or 500 level, brokem
        if int(status_code / 100) >= 4:
            detail = status_code
        # if status code is 200 level and no redirection
        elif (int(status_code/100) == 2 or int(status_code/100) == 3) and final_url_path == url_path:
            detail = 'no redirection'
        # if a non-hompage redirects to a homepage, considered broken
        elif final_url_path == '' and url_path != '':
            detail = 'homepage redirection'
        # if it redirects to another path, we are unsure.
        elif final_url_path != url_path:
            detail = 'non-home redirection'

        # do not know what redirection happens
        else:
            # this list should be empty
            detail = 'unknown redirection'
    else:
        if 'ConnectionError_DNSLookupError' in msg:
            status = 'DNSError'
        elif msg == 'TooManyRedirects':
            status = 'OtherError'
            detail = 'TooManyRedirects'
        else:
            status = 'OtherError'
            detail = 'othererror'
            if "DNS" in detail: status = "DNSError"
    return status, detail


def construct_rand_urls(url):
    """
    Construct random urls from given url. Randomed part satisfies:
        With same format. Consists of the same char format as old ones
        Return urls with all possible random construction
    """
    random_urls = []
    up = urlparse(url)
    def similar_pattern(name):
        sep = "$-_.+!*'(),"
        lower_char = [c for c in name if c.islower()]
        upper_char = [c for c in name if c.isupper()]
        num_char = [c for c in name if c.isdigit()]
        if (len(lower_char) + len(upper_char) + len(num_char)) == 0:
            return ''.join([random.choice(string.ascii_letters) for _ in range(25)])
        else: 
            ratio = ceil(25/(len(lower_char) + len(upper_char) + len(num_char)))
            for c in lower_char:
                name = name.replace(c, ''.join([random.choice(string.ascii_lowercase) for _ in range(ratio)]))
            for c in upper_char:
                name = name.replace(c, ''.join([random.choice(string.ascii_uppercase) for _ in range(ratio)]))
            for c in num_char:
                name = name.replace(c, ''.join([random.choice(string.digits) for _ in range(ratio)]))
            return name
    scheme, netloc, path, query = up.scheme, up.netloc, up.path, up.query
    end_with_slash = False
    if path == '': path += '/'
    elif path != '/' and path[-1] == '/': 
        end_with_slash = True
        path = path[:-1]
    # Filename Random construction
    url_dir, filename = os.path.dirname(path), os.path.basename(path)
    # * Keep the same file ext
    filename, ext = os.path.splitext(filename)
    random_filename = similar_pattern(filename) + ext
    random_url = f"{scheme}://{netloc}{os.path.join(url_dir, random_filename)}"
    if end_with_slash: random_url += '/'
    if query: random_url += '?' + query
    random_urls.append(random_url)
    # Query Random construct
    if not query: return random_urls
    ql = parse_qsl(query)
    if len(ql) == 0: # Not valid query string. Replace all together
        q = similar_pattern(query)
        random_url = f"{scheme}://{netloc}{path}"
        if end_with_slash: random_url += '/'
        random_url += '?' + q
        random_urls.append(random_url)
    else:
        random_urls = []
        for idx, qkv in enumerate(ql):
            qv = similar_pattern(qkv[1])
            query_cp = ql.copy()
            query_cp[idx] = (qkv[0], qv)
            rand_query = '&'.join([f'{q[0]}={q[1]}' for q in query_cp])
            random_url = f"{scheme}://{netloc}{path}"
            if end_with_slash: random_url += '/'
            random_url += '?' + rand_query
            random_urls.append(random_url)
    return random_urls

def change_url_digit(url):
    """
    Detect any parts of path in the middle, if all digits, change with others
    Returns: Applicable urls
    """
    import math
    us = urlsplit(url)
    path = us.path
    if path == '': path = '/'
    parts = path.split('/')
    pos_rpr = []
    for i in range(len(parts)):
        if not parts[i].isnumeric(): continue
        part_d = int(parts[i])
        base_d = 10 ** int(math.log10(part_d)) if part_d > 0 else 0
        if part_d <= base_d: part_d = base_d + 1
        another_d = random.randrange(base_d, part_d)
        new_parts = parts.copy()
        new_parts[i] = str(another_d)
        pos_rpr.append(new_parts)
    return [urlunsplit(us._replace(path='/'.join(pr))) for pr in pos_rpr]

def filter_redir(r):
    """Filter out simple redirections from http --> https"""
    old_his = [h.url for h in r.history] + [r.url]
    new_his = []
    for idx, (h_bef, h_aft) in enumerate(zip(old_his[:-1], old_his[1:])):
        if not h_bef.split('://')[-1] == h_aft.split('://')[-1]:
            new_his.append(r.history[idx])
    return new_his

def text_norm(text):
    filter_char = ' \n\t'
    text = re.sub(f'[{filter_char}]+', ' ', text)
    return text


def broken(url, html=False, ignore_soft_404=False, ignore_soft_404_content=False,
            redir_home=True, recurse=False):
    """
    Entry func: detect whether this url is broken
    html: Require the url to be html.
    ignore_soft_404: Whether soft-404 detection will be ignored
    ignore_soft_404_content: Ignore only content comparison soft-404
    redir_home: If the redir is non-home page to homepage: consider wrong

    Return: True/False/"N/A", reason
    """
    broken_keywords = ['login', 'subscription', 'error', 'notfound', '404', 'badpage', 'not-found', 'not_found', 'suspendedpage.cgi']
    for k in broken_keywords: 
        if k in url: return True, "URL contains broken keyword"

    resp, msg = send_request(url)
    if msg == 'Not Allowed':
        return 'N/A', msg
    status, _ = get_status(url, resp, msg)
    if re.compile('^([45]|DNSError|OtherError)').match(status):
        return True, status
    headers = {k.lower(): v for k, v in resp.headers.items()}
    content_type = headers['content-type'] if 'content-type' in headers else ''
    if html and 'html' not in content_type:
        logger.info('sic transit broken: Not HTML')
        return "N/A", "Not html"
    # elif 'html' not in content_type: # * Not HTML, not detecting soft-404 on Non HTML resource
    #     return True, "Non soft-404 on non-HTML resource"
    if ignore_soft_404:
        return False, "No hard broken"

    # # Ignore Homepages
    # if urlsplit(url).path in ['', '/']:
    #     return False, "Homepage (no Soft-404 detection)"
    final_url = get_canonical(url, resp.text)
    # Non home to home 
    if redir_home:
        if urlsplit(url).path not in ['', '/'] and urlsplit(final_url).path in ['', '/']:
            return True, "Non homepage to homepage"
    try:
        soup = BeautifulSoup(resp.text, 'lxml')
        if len(soup.find_all('link', {'rel': 'canonical'})) > 0:
            if urlsplit(resp.url).path in ['', '/']: raise
            if url_match(url, resp.url):
                return False, "With Canonical"
            # site = he.extract(url)
            # hp, _ = send_request(f'http://{site}')
            # if not url_utils.url_match(hp.url, resp.url):
            #     return False, "With Canonical"
    except: pass
    # Construct new url with random filename
    random_urls = construct_rand_urls(url)
    random_urls += change_url_digit(url)
    broken_decision, reasons = [], []
    # print(random_urls)
    for random_url in random_urls:
        # print(random_url)
        # * If original request no timeout issue, so should be this one
        random_resp, msg = send_request(random_url, timeout=15)
        if msg == 'Not Allowed':
            continue
        random_status, _ = get_status(random_url, random_resp, msg)
        if re.compile('^([45]|DNSError|OtherError)').match(random_status):
            broken_decision.append(False)
            reasons.append("random url hard broken")
            break
        # * Filter out http --> https redirection
        # ? Only consider if both has redirection (even drop this?)
        if len(filter_redir(resp)) != len(filter_redir(random_resp)) and len(filter_redir(resp)) > 0:
            broken_decision.append(False)
            reasons.append("#redirection doesn't match")
            break
        if resp.url == random_resp.url:
            broken_decision.append(True)
            reasons.append("Same final url")
            continue
        # * Content soft-404 comparison
        if not ignore_soft_404_content:
            try:
                url_content = BeautifulSoup(resp.text, 'lxml').get_text(separator=' ')
            except Exception as e:
                url_content = resp.text
            # ? Try to filter case for js oriented page loading
            tokenized_content = text_norm(url_content).split(' ')
            # print(tokenized_content)
            broken_keywords = ['login', 'subscription', 'error', 'notfound', '404', 'badpage', 'not found']
            if len(tokenized_content) < 10:
                for k in broken_keywords:
                    if k in url_content:
                        broken_decision.append(True)
                        reasons.append("short content with broken keywords")
                        return True, reasons
                broken_decision.append(False)
                reasons.append("no features match")
                continue
            try:
                random_content = BeautifulSoup(random_resp.text, 'lxml').get_text(separator=' ')
            except: random_content = random_resp.text
            if k_shingling(text_norm(url_content), text_norm(random_content)) >= 0.9:
                # print(text_norm(url_content), text_norm(random_content))
                broken_decision.append(True)
                reasons.append("Similar soft 404 content")
                continue
        broken_decision.append(False)
        reasons.append("no features match")
        break
    if len(reasons) == 0:
        return 'N/A', 'Guess URLs not allowed'
    else:
        return not False in broken_decision, reasons

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
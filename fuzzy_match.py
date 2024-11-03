import re
from urllib.parse import urlparse
import tldextract
import extract_links


def extract_domain(url):
    ext = tldextract.extract(url)
    return f"{ext.domain}.{ext.suffix}"

def extract_dirnames(url):
    parsed_url = urlparse(url)
    return [part for part in parsed_url.path.split('/') if part]

def generate_regexes(domain, dirs):
    return [
        re.compile(
            rf"https?://(web\.)?archive\.org/web/\d+/https?://[^ ]*{re.escape(domain)}[^ ]*{re.escape(d)}.*",
            re.DOTALL,
        )
        for d in dirs
    ]

def check_if_augmented_strict(broken_link, revision_text):
    archive_pattern = re.compile(r'(https?://(web\.)?archive\.org/web/\d+/)' + re.escape(broken_link))
    match = archive_pattern.search(revision_text)
    if match:
        return match.group(0)
    return ""

def check_if_augmented_fuzzy(broken_link, archived_link):
    # for archived_link in archived_links:
    live_domain = extract_domain(broken_link)
    live_domain.lstrip("www.")
    if live_domain not in archived_link:
        return ""

    live_dirs = extract_dirnames(broken_link)
    regexes = generate_regexes(live_domain, live_dirs)

    match_count = 0
    for regex in regexes:
        if regex.search(archived_link):
            match_count += 1
    if match_count >= len(regexes) // 2:
        return archived_link
    return ""

def find_fuzzy_matched(broken_link, revision_text, fsm):
    if "archived_links" not in fsm:
        fsm["archived_links"] = extract_links.extract_external_links(revision_text)["archived_links"]
    for archived_link in fsm["archived_links"]:
        if check_if_augmented_fuzzy(broken_link, archived_link):
            return archived_link
    return ""

def fuzzy_check(broken_link,  revision_text, fsm):
    # for archived_link in archived_links:
    live_domain = extract_domain(broken_link)
    if live_domain not in revision_text:
        return ""

    live_dirs = extract_dirnames(broken_link)
    regexes = generate_regexes(live_domain, live_dirs)

    match_count = 0
    for regex in regexes:
        if regex.search(revision_text):
            match_count += 1
    if match_count >= len(regexes) // 2:
        return find_fuzzy_matched(broken_link, revision_text, fsm)
    return ""

def check_if_augmented(broken_link, revision_text, fsm):
    revision_text = revision_text.replace("%2F", "/")

    matched = check_if_augmented_strict(broken_link, revision_text)
    if matched:
        return matched
    
    live_domain = extract_domain(broken_link)
    base_match = re.compile(
        rf"https?://(web\.)?archive\.org/web/\d+/https?://[^ ]*{re.escape(live_domain)}[^ ]*",
        re.DOTALL,
    )
    if not base_match.search(revision_text):
        return ""

    return fuzzy_check(broken_link, revision_text, fsm)



def check_if_removed(broken_link, revision_text):
    if broken_link in revision_text:
        return False
    if broken_link.startswith("http://") and broken_link[7:] in revision_text:
        return False
    if '#' in broken_link and broken_link.split('#')[0] in revision_text:
        return False
    return True




# live_link = "http://crosstree.info/Documents/Care%20of%20F%20n%20V.pdf"
# revision_text = """
# The archived link matches the regular link.

# http://www.rkv.rgukt.in/content/Biology/47Module/47fruit.pdf
# {{other uses}}
# {{pp-semiprotected|small=yes}}
# {{pp-move-indef}}
# {{short description|Seed-bearing part of a flowering plant}}
# [[File:Culinary fruits front view.jpg|thumb|[[List of culinary fruits|Culinary fruits]]]]

# In [[botany]], a '''fruit''' is the [[seed]]-bearing structure in [[flowering plant]]s (also known as angiosperms) formed from the [[Ovary (plants)|ovary]] after [[flowering plant|flowering]].

# Fruits are the means by which angiosperms disseminate [[seed]]s. Edible fruits, in particular, have propagated with the movements of humans and animals in a [[Symbiosis|symbiotic relationship]] as a means for [[seed dispersal]] and [[nutrition]]; in fact, humans and many animals have become dependent on fruits as a source of food.<ref name="Lewis375">{{cite book |last=Lewis |first=Robert A. |title=CRC Dictionary of Agricultural Sciences |url=https://books.google.com/books?id=TwRUZK0WTWAC&pg=PA375&lpg=PA375&dq=fruit |year=2002 |publisher=[[CRC Press]] |isbn=978-0-8493-2327-0}}</ref> Accordingly, fruits account for a substantial fraction of the world's [[agriculture|agricultural]] output, and some (such as the [[apple]] and the [[pomegranate]]) have acquired extensive cultural and symbolic meanings.

# In common language usage, "fruit" normally means the fleshy seed-associated structures of a plant that are sweet or sour, and edible in the raw state, such as [[apple]]s, [[banana]]s, [[grape]]s, [[lemon]]s, [[Orange (fruit)|oranges]], and [[Strawberry|strawberries]]. On the other hand, in botanical usage, "fruit" includes many structures that are not commonly called "fruits", such as [[bean]] pods, [[maize|corn]] [[Seed|kernels]], [[tomato]]es, and [[wheat]] grains.<ref>{{cite book |last=Schlegel |first=Rolf H J |title=Encyclopedic Dictionary of Plant Breeding and Related Subjects |url=https://books.google.com/books?id=7J-3fD67RqwC&pg=PA177&lpg=PA177&vq=fruit&dq=acarpous |year=2003 |publisher=Haworth Press |isbn=978-1-56022-950-6 |page=177}}</ref><ref name="Mauseth271">{{cite book |last=Mauseth |first=James D. |title=Botany: An Introduction to Plant Biology |url=https://books.google.com/books?id=0DfYJsVRmUcC&pg=PA271&lpg=PA271 |year=2003 |publisher=Jones and Bartlett |isbn=978-0-7637-2134-3 |pages=271–72}}</ref> The section of a [[fungus]] that produces [[spore]]s is also called a fruiting body.<ref>{{cite web |url=http://www.britannica.com/EBchecked/topic/560984/sporophore |title=Sporophore from Encyclopædia Britannica |url-status=live |archiveurl=https://web.archive.org/web/20110222204440/http://www.britannica.com/EBchecked/topic/560984/sporophore |archivedate=2011-02-22 }}</ref>

# == Botanic fruit and culinary fruit ==
# [[File:Botanical Fruit and Culinary Vegetables.png|thumb|[[Venn diagram]] representing the relationship between (culinary) vegetables and botanical fruits{{citation needed|date=February 2016}}]]
# Many common terms for seeds and fruit do not correspond to the botanical classifications. In culinary terminology, a [[List of culinary fruits|''fruit'']] is usually any sweet-tasting plant part, especially a botanical fruit; a ''nut'' is any hard, oily, and shelled plant product; and a ''[[vegetable]]'' is any [[Umami|savory]] or less sweet plant product.<ref>For a [[Supreme Court of the United States]] ruling on the matter, see [[Nix v. Hedden]].</ref> However, in botany, a ''fruit'' is the ripened ovary or carpel that contains seeds, a ''[[Nut (fruit)|nut]]'' is a type of fruit and not a seed, and a ''seed'' is a ripened ovule.<ref name="McGee247" />

# Examples of culinary "vegetables" and nuts that are botanically fruit include [[maize|corn]], [[cucurbitaceae|cucurbits]] (e.g., [[cucumber]], [[pumpkin]], and [[Squash (plant)|squash]]), [[eggplant]], [[legume]]s ([[bean]]s, [[peanut]]s, and [[pea]]s), sweet [[bell pepper|pepper]], and [[tomato]]. In addition, some [[spice]]s, such as [[allspice]] and [[chili pepper]], are fruits, botanically speaking.<ref name="McGee247">{{cite book |last=McGee |first=Harold |authorlink=Harold McGee |title=On Food and Cooking: The Science and Lore of the Kitchen |url=https://books.google.com/books?id=iX05JaZXRz0C&pg=PA247&lpg=PA247&vq=Fruit&dq=On+Food+And+Cooking |year=2004 |publisher=[[Simon & Schuster]] |isbn=978-0-684-80001-1 |pages=247–48}}</ref> In contrast, [[rhubarb]] is often referred to as a fruit, because it is used to make sweet desserts such as [[pies]], though only the [[petiole (botany)|petiole]] (leaf stalk) of the rhubarb plant is edible,<ref>{{cite book |last=McGee |title=On Food and Cooking |url=https://books.google.com/books?id=iX05JaZXRz0C&pg=PA367&lpg=PA367&vq=rhubarb&dq=On+Food+And+Cooking |page=367 |isbn=978-0-684-80001-1 |year=2004}}</ref> and edible [[gymnosperm]] seeds are often given fruit names, e.g., [[Ginkgo biloba|ginkgo]] nuts and [[pine nut]]s.

# Botanically, a [[cereal]] grain, such as [[maize|corn]], [[rice]], or [[wheat]], is also a kind of fruit, termed a [[caryopsis]]. However, the fruit wall is very thin and is fused to the seed coat, so almost all of the edible grain is actually a seed.<ref>{{cite book |last=Lewis |title=CRC Dictionary of Agricultural Sciences |url=https://books.google.com/books?id=TwRUZK0WTWAC&pg=PA238&lpg=PA238&vq=cereal&dq=fruit |page=238 |isbn=978-0-8493-2327-0 |year=2002}}</ref>

# == Structure ==
# {{Main|Fruit anatomy}}
# The outer, often edible layer, is the ''pericarp'', formed from the ovary and surrounding the seeds, although in some species other tissues contribute to or form the edible portion. The pericarp may be described in three layers from outer to inner, the ''epicarp'', ''mesocarp'' and ''endocarp''.

# Fruit that bears a prominent pointed terminal projection is said to be ''beaked''.<ref>{{cite web|url=https://florabase.dpaw.wa.gov.au/help/glossary#B|title=Glossary of Botanical Terms|work=FloraBase|publisher=Western Australian Herbarium|accessdate=23 July 2014|url-status=live|archiveurl=https://web.archive.org/web/20141008190434/https://florabase.dpaw.wa.gov.au/help/glossary#B|archivedate=8 October 2014}}</ref>

# == Development ==
# [[File:Nectarine Fruit Development.jpg|thumb|The development sequence of a typical [[drupe]], the [[nectarine]] (''Prunus persica'') over a 7.5 month period, from bud formation in early winter to fruit [[ripening]] in midsummer (see [[:File:Nectarine Fruit Development.jpg|image page]] for further information)]]

# A fruit results from maturation of one or more flowers, and the [[gynoecium]] of the flower(s) forms all or part of the fruit.<ref>Esau, K. 1977. ''Anatomy of seed plants''. John Wiley and Sons, New York.</ref>

# Inside the ovary/ovaries are one or more [[ovule]]s where the [[megagametophyte]] contains the egg cell.<ref>[http://www.palaeos.com/Plants/Lists/Glossary/GlossaryL.html#M] {{webarchive |url=https://web.archive.org/web/20101220200017/http://www.palaeos.com/Plants/Lists/Glossary/GlossaryL.html#M |date=December 20, 2010 }}</ref><!--January 2012, the http://palaeos.com/ web site requests that links like this not be corrected until their major overhaul is completed and a public announcement made.--> After [[double fertilization]], these ovules will become seeds. The ovules are fertilized in a process that starts with [[pollination]], which involves the movement of pollen from the stamens to the stigma of flowers. After pollination, a tube grows from the pollen through the stigma into the ovary to the ovule and two sperm are transferred from the pollen to the megagametophyte. Within the megagametophyte one of the two sperm unites with the egg, forming a [[zygote]], and the second sperm enters the central cell forming the endosperm mother cell, which completes the double fertilization process.<ref>{{cite book |author=Mauseth, James D. |title=Botany: an introduction to plant biology |year=2003 |publisher=Jones and Bartlett Publishers |location=Boston |isbn=978-0-7637-2134-3 |page=258}}</ref><ref>{{cite book |author1=Rost, Thomas L. |author2=Weier, T. Elliot |author3=Weier, Thomas Elliot |title=Botany: a brief introduction to plant biology |year=1979 |publisher=Wiley |location=New York |isbn=978-0-471-02114-8 |pages=[https://archive.org/details/botanybriefintro00rost/page/135 135–37] |url=https://archive.org/details/botanybriefintro00rost/page/135 }}</ref> Later the zygote will give rise to the embryo of the seed, and the endosperm mother cell will give rise to [[endosperm]], a nutritive tissue used by the embryo.

# As the ovules develop into seeds, the ovary begins to ripen and the ovary wall, the ''pericarp'', may become fleshy (as in berries or [[drupe]]s), or form a hard outer covering (as in nuts). In some multiseeded fruits, the extent to which the flesh develops is proportional to the number of fertilized ovules.<ref>{{cite book |last=Mauseth |title=Botany |url=https://books.google.com/books?id=0DfYJsVRmUcC&pg=PP14&lpg=PP11 |pages=Chapter 9: Flowers and Reproduction |nopp=true |isbn=978-0-7637-2134-3 |year=2003}}</ref> The pericarp is often differentiated into two or three distinct layers called the ''exocarp'' (outer layer, also called epicarp), ''mesocarp'' (middle layer), and ''endocarp'' (inner layer). In some fruits, especially simple fruits derived from an [[inferior ovary]], other parts of the flower (such as the floral tube, including the [[petal]]s, [[sepal]]s, and [[stamen]]s), fuse with the ovary and ripen with it. In other cases, the sepals, petals and/or stamens and [[Gynoecium|style]] of the flower fall off. When such other floral parts are a significant part of the fruit, it is called an ''[[accessory fruit]]''. Since other parts of the flower may contribute to the structure of the fruit, it is important to study flower structure to understand how a particular fruit forms.<ref name="Mauseth271" />

# There are three general modes of fruit development:
# * Apocarpous fruits develop from a single flower having one or more separate carpels, and they are the simplest fruits.
# * Syncarpous fruits develop from a single gynoecium having two or more carpels fused together.
# * Multiple fruits form from many different flowers.

# Plant scientists have grouped fruits into three main groups, simple fruits, aggregate fruits, and composite or multiple fruits.<ref name="plants_systematics">{{cite book |last1= Singh |first1= Gurcharan |title= Plants Systematics: An Integrated Approach |url= https://books.google.com/books?id=In_Lv8iMt24C&pg=PA83 |year= 2004 |publisher= Science Publishers |isbn= 978-1-57808-351-0 |page= 83 }}</ref> The groupings are not evolutionarily relevant, since many diverse plant [[taxa]] may be in the same group, but reflect how the flower organs are arranged and how the fruits develop.

# === Simple fruit ===
# [[File:DewberriesWeb.jpg|thumb|upright|[[Dewberry]] flowers. Note the multiple [[pistil]]s, each of which will produce a [[drupe]]let. Each flower will become a blackberry-like [[aggregate fruit]].]]

# Simple fruits can be either dry or fleshy, and result from the ripening of a simple or compound ovary in a flower with only one [[Carpel|pistil]]. Dry fruits may be either [[dehiscent]] (they open to discharge seeds), or indehiscent (they do not open to discharge seeds).<ref>{{cite book |last=Schlegel |title=Encyclopedic Dictionary |url=https://books.google.com/books?id=7J-3fD67RqwC&dq=acarpous&pg=PA123&lpg=PA123
# |page=123 |isbn=978-1-56022-950-6 |year=2003}}</ref> Types of dry, simple fruits, and examples of each, include:
# * [[achene]] – most commonly seen in aggregate fruits (e.g., [[strawberry]])
# * [[Capsule (fruit)|capsule]] – (e.g., [[Brazil nut]])
# * [[caryopsis]] – (e.g., [[wheat]])
# * [[Achene|cypsela]] – an achene-like fruit derived from the individual florets in a [[Head (botany)|capitulum]] (e.g., [[dandelion]]).
# * [[drupe|fibrous drupe]] – (e.g., [[coconut]], [[walnut]])
# * [[Follicle (fruit)|follicle]] – is formed from a single carpel, opens by one suture (e.g., [[milkweed]]), commonly seen in aggregate fruits (e.g., [[magnolia]])
# * [[legume]] – (e.g., [[bean]], [[pea]], [[peanut]])
# * [[loment]] – a type of [[indehiscent]] legume
# * [[Nut (fruit)|nut]] – (e.g., [[beech]], [[hazelnut]], oak [[acorn]])
# * [[samara (fruit)|samara]] – (e.g., [[Ash tree|ash]], [[elm]], [[maple]] key)
# * [[schizocarp]] – (e.g., [[carrot]] seed)
# * [[silique]] – (e.g., [[radish]] seed)
# * [[silicle]] – (e.g., [[shepherd's purse]])
# * [[utricle (fruit)|utricle]] – (e.g., strawberry)

# Fruits in which part or all of the ''pericarp'' (fruit wall) is fleshy at maturity are ''simple fleshy fruits''. Types of simple, fleshy, fruits (with examples) include:
# * [[berry (botany)|berry]] – (e.g., [[cranberry]], [[gooseberry]], [[redcurrant]], [[tomato]])
# * stone fruit or [[drupe]] (e.g., [[apricot]], [[cherry]], [[olive]], [[peach]], [[plum]])
# <!-- This section is linked from [[Rose]] -->

# An aggregate fruit, or ''etaerio'', develops from a single flower with numerous simple pistils.<ref>{{cite book |last=Schlegel |title=Encyclopedic Dictionary |url=https://books.google.com/books?id=7J-3fD67RqwC&pg=PA16&lpg=PA16&vq=Aggregate+fruit&dq=acarpous
# |page=16 |isbn=978-1-56022-950-6 |year=2003}}</ref>
# * [[Magnolia]] and [[peony]], collection of follicles developing from one flower.
# * [[Sweet gum]], collection of capsules.
# * [[Sycamore]], collection of achenes.
# * [[Teasel]], collection of cypsellas
# * [[Tuliptree]], collection of samaras.

# The [[pome]] fruits of the family [[Rosaceae]], (including [[apple]]s, [[pear]]s, [[rosehip]]s, and [[saskatoon berry]]) are a syncarpous fleshy fruit, a simple fruit, developing from a half-inferior ovary.<ref name="evolutionary_trends_in_flowering_plants">{{cite book |title= Evolutionary trends in flowering plants |url= https://books.google.com/books?id=c11HBwElG-4C&pg=PA209 |year= 1991 |publisher= Columbia University Press |location= New York |isbn= 978-0-231-07328-8 |page= 209 }}</ref>

# [[Schizocarp]] fruits form from a syncarpous ovary and do not really [[dehiscence (botany)|dehisce]], but rather split into segments with one or more seeds; they include a number of different forms from a wide range of families.<ref name="plants_systematics" /> Carrot seed is an example.
# [[File:Lilyfruit.jpg|upright|thumb|''[[Lilium]]'' unripe capsule fruit]]

# === Aggregate fruit ===
# {{Main|Aggregate fruit}}
# [[File:Longitudinal section of raspberry flower.gif|thumb|Detail of raspberry [[flower]]]]
# Aggregate fruits form from single flowers that have multiple carpels which are not joined together, i.e. each pistil contains one carpel. Each pistil forms a fruitlet, and collectively the fruitlets are called an etaerio. Four types of aggregate fruits include etaerios of achenes, follicles, drupelets, and berries. Ranunculaceae species, including ''[[Clematis]]'' and ''[[Ranunculus]]'' have an etaerio of achenes, ''[[Calotropis]]'' has an etaerio of follicles, and ''[[Rubus]]'' species like raspberry, have an etaerio of drupelets. ''[[Annona]]'' have an etaerio of berries.<ref name=Gupta>{{cite book |title=Genetics Classical To Modern|url=https://books.google.com/books?id=uIfSEdff6YgC&pg=RA1-PA2134#v=onepage|author= Gupta, Prof. P.K. |publisher= Rastogi Publication |pages= 2–134 |isbn= 978-81-7133-896-2|year=2007}}</ref><ref>http://www.rkv.rgukt.in/content/Biology/47Module/47fruit.pdf {{dead link|date=March 2013|fix-attempted=yes}}</ref>

# The [[raspberry]], whose pistils are termed ''drupelets'' because each is like a small [[drupe]] attached to the receptacle. In some [[bramble]] fruits (such as [[blackberry]]) the receptacle is elongated and part of the ripe fruit, making the blackberry an ''aggregate-accessory'' fruit.<ref>{{cite book |last=McGee |title=On Food and Cooking |url=https://books.google.com/books?id=iX05JaZXRz0C&pg=PA361&lpg=PA361&vq=raspberry&dq=On+Food+And+Cooking |pages=361–62 |isbn=978-0-684-80001-1 |year=2004}}</ref> The [[strawberry]] is also an aggregate-accessory fruit, only one in which the seeds are contained in [[achene]]s.<ref>{{cite book |last=McGee |title=On Food and Cooking |url=https://books.google.com/books?id=iX05JaZXRz0C&pg=PA364&lpg=PA364&vq=strawberry&dq=On+Food+And+Cooking |pages=364–65 |isbn=978-0-684-80001-1 |year=2004}}</ref> In all these examples, the fruit develops from a single flower with numerous pistils.

# === Multiple fruits ===
# {{Main|Multiple fruit}}
# A multiple fruit is one formed from a cluster of flowers (called an ''[[inflorescence]]''). Each flower produces a fruit, but these mature into a single mass.<ref>{{cite book |last=Schlegel |title=Encyclopedic Dictionary |url=https://books.google.com/books?id=7J-3fD67RqwC&pg=PA282&lpg=PA282&vq=Multiple+fruit&dq=acarpous |page=282 |isbn=978-1-56022-950-6 |year=2003}}</ref> Examples are the [[pineapple]], [[ficus|fig]], [[mulberry]], [[osage-orange]], and [[breadfruit]].

# [[File:Noni fruit dev.jpg|thumb|In some plants, such as this [[noni]], flowers are produced regularly along the stem and it is possible to see together examples of flowering, fruit development, and fruit ripening.]]
# In the photograph on the right, stages of flowering and fruit development in the [[noni]] or Indian mulberry (''Morinda citrifolia'') can be observed on a single branch. First an inflorescence of white flowers called a head is produced. After [[Fertilization#Fertilisation in plants|fertilization]], each flower develops into a drupe, and as the drupes expand, they become ''connate'' (merge) into a ''multiple fleshy fruit'' called a ''syncarp''.

# === Berries ===
# {{Main|Berry (botany)|Berry}}
# Berries are another type of fleshy fruit; they are simple fruit created from a single ovary.<ref>{{Cite book|url=https://books.google.com/books?id=1qwuBXeczzgC&pg=PT56&dq=berry+type+of+fleshy+fruit+are+simple+fruit+created+from+single+ovary|title=Handbook of Fruits and Fruit Processing|last=Sinha|first=Nirmal|last2=Sidhu|first2=Jiwan|last3=Barta|first3=Jozsef|last4=Wu|first4=James|last5=Cano|first5=M. Pilar|year=2012|publisher=John Wiley & Sons|isbn=978-1-118-35263-2}}</ref> The ovary may be compound, with several carpels. Types include (examples follow in the table below):
# * [[Pepo (botany)|Pepo]] – berries whose skin is hardened, [[Cucurbitaceae|cucurbits]]
# * [[Hesperidium]] – berries with a rind and a juicy interior, like most [[citrus]] fruit

# === Accessory fruit ===
# [[File:Pineapple and cross section.jpg|thumb|right|The fruit of a pineapple includes tissue from the [[sepal]]s as well as the [[pistil]]s of many flowers. It is an [[accessory fruit]] and a [[multiple fruit]].]]
# {{Main|Accessory fruit}}
# Some or all of the edible part of accessory fruit is not generated by the ovary. Accessory fruit can be simple, aggregate, or multiple, i.e., they can include one or more pistils and other parts from the same flower, or the pistils and other parts of many flowers.

# === Table of fruit examples ===
# {| class="wikitable"
# |+ Types of fleshy fruits
# |-
# ! True berry
# ! Pepo
# ! Hesperidium
# ! Aggregate fruit
# ! Multiple fruit
# ! Accessory fruit
# |-
# | [[Banana]], [[Blackcurrant]], [[Blueberry]], [[Chili pepper]], [[Cranberry]], [[Eggplant]], [[Gooseberry]], [[Grape]], [[Guava]], [[Kiwifruit]], [[Lucuma]], [[Pomegranate]], [[Redcurrant]], [[Tomato]]
# | [[Cucumber]], [[Gourd]], [[Melon]], [[Pumpkin]]
# | [[Grapefruit]], [[Lemon]], [[Lime (fruit)|Lime]], [[Orange (fruit)|Orange]]
# | [[Blackberry]], [[Boysenberry]], [[Raspberry]]
# | [[ficus|Fig]], [[Hedge apple]], [[Mulberry]], [[Pineapple]]
# | [[Apple]], [[Pineapple]], [[Rose hip]], [[prunus|Stone fruit]], [[Strawberry]]
# |}

# == Seedless fruits ==
# [[File:Dish with fruits.jpg|thumb|Some seedless fruits]]
# [[File:FruitArrangement.jpg|thumb|An arrangement of fruits commonly thought of as vegetables, including [[tomato]]es and various [[Squash (fruit)|squash]]]]
# Seedlessness is an important feature of some fruits of commerce. Commercial [[cultivar]]s of [[banana]]s and [[pineapple]]s are examples of [[seedless fruit]]s. Some cultivars of [[citrus]] fruits (especially [[grapefruit]], [[mandarin orange]]s, navel [[Orange (fruit)|oranges]]), [[Mikan|satsumas]], [[table grape]]s, and [[watermelon]]s are valued for their seedlessness. In some species, seedlessness is the result of ''[[parthenocarpy]]'', where fruits set without fertilization. Parthenocarpic fruit set may or may not require pollination, but most seedless citrus fruits require a stimulus from pollination to produce fruit.

# Seedless bananas and grapes are [[triploid]]s, and seedlessness results from the abortion of the [[embryo]]nic plant that is produced by fertilization, a phenomenon known as ''[[stenospermocarpy]]'', which requires normal pollination and fertilization.<ref name="Spiegel87">{{cite book |last=Spiegel-Roy |first=P. |author2=E.E. Goldschmidt |title=The Biology of Citrus |url=https://books.google.com/books?id=SmRJnd73dbYC&pg=PA87&lpg=PA87&dq=parthenocarpy |year=1996 |publisher=[[Cambridge University Press]] |isbn=978-0-521-33321-4 |pages=87–88}}</ref>

# == Seed dissemination ==
# Variations in fruit structures largely depend on their seeds' [[Biological dispersal|mode of dispersal]]. This dispersal can be achieved by animals, [[explosive dehiscence]], water, or wind.<ref name="Capon198">{{cite book |last=Capon |first=Brian |title=Botany for Gardeners |url=https://books.google.com/books?id=Z2s9v__6rp4C&pg=PA198&lpg=PA198&dq=coconut+dispersal |year=2005 |publisher=Timber Press |isbn=978-0-88192-655-2 |pages=198–99}}</ref>

# Some fruits have coats covered with spikes or hooked burrs, either to prevent themselves from being eaten by [[animal]]s, or to stick to the feathers, hairs, or legs of animals, using them as dispersal agents. Examples include [[cocklebur]] and [[unicorn plant]].<ref>{{cite book |last=Heiser |first=Charles B. |title=Weeds in My Garden: Observations on Some Misunderstood Plants |url=https://books.google.com/books?id=nN1ohECdSC8C&pg=PA93&lpg=PA93&dq=cocklebur |year=2003 |publisher=Timber Press |isbn=978-0-88192-562-3 |pages=93–95}}</ref><ref>{{cite book |last=Heiser |title=Weeds in My Garden |url=https://books.google.com/books?id=nN1ohECdSC8C&pg=PA164&lpg=PA162&vq=unicorn&dq=cocklebur |pages=162–64 |isbn=978-0-88192-562-3 |year=2003}}</ref>

# The sweet flesh of many fruits is "deliberately" appealing to animals, so that the seeds held within are eaten and "unwittingly" carried away and deposited (i.e., [[Defecation|defecated]]) at a distance from the parent. Likewise, the nutritious, oily kernels of [[Nut (fruit)|nuts]] are appealing to rodents (such as [[squirrel]]s), which [[hoarding|hoard]] them in the soil to avoid starving during the winter, thus giving those seeds that remain uneaten the chance to [[Germination|germinate]] and grow into a new plant away from their parent.<ref name="McGee247" />

# Other fruits are elongated and flattened out naturally, and so become thin, like [[wing]]s or [[helicopter]] blades, e.g., [[elm]], [[maple]], and [[tuliptree]]. This is an [[evolution]]ary mechanism to increase dispersal distance away from the parent, via wind. Other wind-dispersed fruit have tiny "[[Pappus (flower structure)|parachutes]]", e.g., [[dandelion]], [[Asclepias|milkweed]], [[Tragopogon|salsify]].<ref name="Capon198" />

# [[Coconut]] fruits can float thousands of miles in the ocean to spread seeds. Some other fruits that can disperse via water are [[nipa palm]] and [[screw pine]].<ref name="Capon198" />

# Some fruits fling seeds substantial distances (up to 100&nbsp;m in [[sandbox tree]]) via [[explosive dehiscence]] or other mechanisms, e.g., [[impatiens]] and [[squirting cucumber]].<ref>{{cite book |last=Feldkamp |first=Susan |title=Modern Biology |url=https://archive.org/details/modernbiology00feld |url-access=registration |year=2002 |publisher=Holt, Rinehart, and Winston |isbn=978-0-88192-562-3 |page=[https://archive.org/details/modernbiology00feld/page/634 634]}}</ref>

# == Food uses ==

# Many hundreds of fruits, including fleshy fruits (like [[apple]], [[kiwifruit]], [[mango]], [[peach]], [[pear]], and [[watermelon]]) are commercially valuable as [[human]] food, eaten both fresh and as jams, marmalade and other [[food preservation|preserves]]. Fruits are also used in manufactured foods (e.g., [[cake]]s, [[cookie]]s, [[ice cream]], [[muffin]]s, or [[yogurt]]) or beverages, such as fruit juices (e.g., [[apple juice]], [[grape juice]], or [[orange juice]]) or [[alcoholic beverages]] (e.g., [[brandy]], [[fruit beer]], or [[wine]]).<ref>{{cite book |last=McGee |title=On Food and Cooking |url=https://books.google.com/books?id=iX05JaZXRz0C&pg=PA350&lpg=PA350 |pages=Chapter 7: A Survey of Common Fruits |nopp=true |isbn=978-0-684-80001-1 |year=2004}}</ref> Fruits are also used for gift giving, e.g., in the form of [[Fruit Basket]]s and [[Fruit Bouquet]]s.

# Many "vegetables" in culinary ''parlance''  are botanical fruits, including [[bell pepper]], [[cucumber]], [[eggplant]], [[green bean]], [[okra]], [[pumpkin]], [[Squash (fruit)|squash]], [[tomato]],  and [[zucchini]].<ref>{{cite book |last=McGee |title=On Food and Cooking |url=https://books.google.com/books?id=iX05JaZXRz0C&pg=PA300&lpg=PA299 |pages=Chapter 6: A Survey of Common Vegetables |nopp=true |isbn=978-0-684-80001-1 |year=2004}}</ref> [[Olive]] fruit is pressed for [[olive oil]]. Spices like [[allspice]], [[black pepper]], [[paprika]], and [[vanilla]] are derived from berries.<ref>{{cite book |last=Farrell |first=Kenneth T. |title=Spices, Condiments and Seasonings |url=https://books.google.com/books?id=ehAFUhWV4QMC&pg=PA17&lpg=PA17 |year=1999 |publisher=Springer |isbn=978-0-8342-1337-1 |pages=17–19}}</ref>

# === Storage ===
# All fruits benefit from proper post harvest care, and in many fruits, the plant hormone [[Ethylene-ripened fruits|ethylene]] causes [[ripening]]. Therefore, maintaining most fruits in an efficient [[cold chain]] is optimal for post harvest storage, with the aim of extending and ensuring shelf life.<ref name=pxkf>Why Cold Chain for Fruits: {{cite web |first= Pawanexh |last= Kohli |year= 2008 |title= Fruits and Vegetables Post-Harvest Care: The Basics |url= http://crosstree.info/Documents/Care%20of%20F%20n%20V.pdf |publisher= Crosstree Techno-visors |url-status= dead |archiveurl= https://web.archive.org/web/20161204061346/http://www.crosstree.info/Documents/Care |archivedate= 2016-12-04 |access-date= 2009-09-28 }}</ref>

# === Nutritional value ===
# [[File:Fruit Nutrition.png|thumb|upright=1.8|Each point refers to a 100&nbsp;g serving of the fresh fruit, the daily recommended allowance of vitamin C is on the X axis and mg of Potassium (K) on the Y (offset by 100 mg which every fruit has) and the size of the disk represents amount of fiber (key in upper right). Watermelon, which has almost no fiber, and low levels of vitamin C and potassium, comes in last place.]]

# As excessive intake of [[added sugar]] is harmful and fruits are relatively high in [[sugar]] it is often questioned whether fruits are actually healthy food. It is in fact difficult to get excessive amounts of sugar (e. g. [[fructose]]) from fruits as they also contain fibers, water and have significant chewing resistance. An overview on numerous studies can be found here.<ref>{{Cite web|title=Is Fruit Good or Bad for Your Health? The Sweet Truth|url=https://www.healthline.com/nutrition/is-fruit-good-or-bad-for-your-health|website=Healthline|language=en|access-date=2020-05-03}}</ref> Studies show that fruits are very satisfying (for example apples or oranges).<ref>{{Cite journal|last=Holt|first=S. H.|last2=Miller|first2=J. C. |last3=Petocz|first3=P. |last4=Farmakalidis|first4=E.|date=September 1995 |title=A satiety index of common foods|journal=European Journal of Clinical Nutrition|volume=49 |issue=9|pages=675–690|issn=0954-3007|pmid=7498104}}</ref> In addition, the fibres contained in fruits promote [[satiety]]<ref>{{Cite journal|last=Slavin|first=J.|last2=Green|first2=H.|date=March 2007|title=Dietary fibre and satiety|journal=Nutrition Bulletin|language=en|volume=32|issue=s1|pages=32–42 |doi=10.1111/j.1467-3010.2007.00603.x|issn=1471-9827}}</ref> and help lose weight<ref>{{Cite journal|last=Salas-Salvadó|first=Jordi |last2=Farrés|first2=Xavier|last3=Luque|first3=Xavier |last4=Narejos|first4=Silvia|last5=Borrell|first5=Manel |last6=Basora|first6=Josep|last7=Anguera|first7=Anna|last8=Torres|first8=Ferran |last9=Bulló|first9=Mònica|last10=Balanza|first10=Rafel|last11=Fiber in Obesity-Study Group|date=June 2008|title=Effect of two doses of a mixture of soluble fibres on body weight and metabolic variables in overweight or obese patients: a randomised trial|journal=The British Journal of Nutrition|volume=99|issue=6|pages=1380–1387 |doi=10.1017/S0007114507868528|issn=1475-2662|pmid=18031592|doi-access=free}}</ref> and have [[cholesterol-lowering effects]].<ref>{{Cite journal|last=Brown|first=L.|last2=Rosner|first2=B.|last3=Willett|first3=W. W.|last4=Sacks|first4=F. M.|date=January 1999|title=Cholesterol-lowering effects of dietary fiber: a meta-analysis|journal=The American Journal of Clinical Nutrition|volume=69|issue=1|pages=30–42|doi=10.1093/ajcn/69.1.30|issn=0002-9165|pmid=9925120|doi-access=free}}</ref>

# Fresh fruits are generally high in [[fiber]], [[vitamin C]], and [[water]].<ref name=Hulme1970>{{cite journal |year=1970 |author=Hulme, A.C (editor) |title=The Biochemistry of Fruits and their Products |volume= 1 |place=London & New York |publisher=Academic Press }}</ref>

# Regular consumption of fruit is generally associated with reduced risks of several diseases and functional declines associated with aging.<ref>{{Cite journal|last=Lim|first=Stephen S.|last2=Vos|first2=Theo|last3=Flaxman|first3=Abraham D.|last4=Danaei|first4=Goodarz|last5=Shibuya|first5=Kenji|last6=Adair-Rohani|first6=Heather|last7=Amann|first7=Markus|last8=Anderson|first8=H. Ross|last9=Andrews|first9=Kathryn G.|date=2012-12-15|title=A comparative risk assessment of burden of disease and injury attributable to 67 risk factors and risk factor clusters in 21 regions, 1990-2010: a systematic analysis for the Global Burden of Disease Study 2010|journal=Lancet|volume=380|issue=9859|pages=2224–60|doi=10.1016/S0140-6736(12)61766-8|issn=1474-547X|pmc=4156511|pmid=23245609}}</ref><ref>{{cite journal|journal=BMJ|year=2014|issue=Jul 29|volume=349|page=g4490|doi=10.1136/bmj.g4490|title= Fruit and vegetable consumption and mortality from all causes, cardiovascular disease, and cancer: systematic review and dose-response meta-analysis of prospective cohort studies|authors=Wang X, Ouyang Y, Liu J, Zhu M, Zhao G, Bao W, Hu FB|pmid=25073782|pmc=4115152}}</ref> A current review of meta-analyses even comes to the conclusion that current assessments might even significantly underestimate the protective associations of fruit and vegetable intakes.<ref>{{Cite journal|last=Yip|first=Cynthia Sau Chun|last2=Chan|first2=Wendy|last3=Fielding|first3=Richard|date=March 2019|title=The Associations of Fruit and Vegetable Intakes with Burden of Diseases: A Systematic Review of Meta-Analyses|journal=Journal of the Academy of Nutrition and Dietetics|volume=119|issue=3|pages=464–481|doi=10.1016/j.jand.2018.11.007|issn=2212-2672|pmid=30639206}}</ref>

# === Food safety ===
# For [[food safety]], the [[Centers for Disease Control and Prevention|CDC]] recommends proper fruit handling and preparation to reduce the risk of [[food contamination]] and [[foodborne illness]]. Fresh fruits and vegetables should be carefully selected;  at the store, they should not be damaged or bruised; and precut pieces should be refrigerated or surrounded by ice.

# All fruits and vegetables should be rinsed before eating. This recommendation also applies to produce with rinds or skins that are not eaten. It should be done just before preparing or eating to avoid premature spoilage.

# Fruits and vegetables should be kept separate from raw foods like meat, poultry, and seafood, as well as from utensils that have come in contact with raw foods. Fruits and vegetables that are not going to be cooked should be thrown away if they have touched raw meat, poultry, seafood, or eggs.

# All cut, peeled, or cooked fruits and vegetables should be refrigerated within two hours. After a certain time, harmful bacteria may grow on them and increase the risk of foodborne illness.<ref name=cdc>{{cite web|url=http://www.fruitsandveggiesmatter.gov/health_professionals/food_safety.html|title=Nutrition for Everyone: Fruits and Vegetables – DNPAO – CDC|work=fruitsandveggiesmatter.gov|url-status=dead|archiveurl=https://web.archive.org/web/20090509004401/http://www.fruitsandveggiesmatter.gov/health_professionals/food_safety.html|archivedate=2009-05-09}}</ref>

# === Allergies ===
# Fruit allergies make up about 10 percent of all food related allergies.<ref>{{cite web |url=http://www.aafa.org/display.cfm?id=9&sub=20&cont=286 |title=Asthma and Allergy Foundation of America |publisher=Aafa.org |accessdate=2014-04-25 |url-status=dead |archiveurl=https://web.archive.org/web/20121006052320/http://aafa.org/display.cfm?id=9&sub=20&cont=286# |archivedate=2012-10-06 }}</ref><ref>{{cite book|url=https://books.google.com/books?id=qS8DqmZLHPUC&pg=PA171&dq=fruit+peel+allergen#v=onepage |title=The Wellness Project |author=Roy Mankovitz |publisher= |date=2010 |accessdate=2014-04-25|isbn=978-0-9801584-4-1 }}</ref>

# == Nonfood uses ==
# Because fruits have been such a major part of the human diet, various cultures have developed many different uses for fruits they do not depend on for food. For example:
# * [[Bayberry]] fruits provide a wax often used to make candles;<ref>{{cite book |last=K |first=Amber |title=Candlemas: Feast of Flames |url=https://books.google.com/books?id=WQL4W13EYlUC&pg=PA155&lpg=PA155&dq=bayberry |date=December 1, 2001 |publisher=Llewellyn Worldwide |isbn=978-0-7387-0079-3 |page=155}}</ref>
# * Many dry fruits are used as decorations or in dried flower arrangements (e.g., [[annual honesty]], [[cotoneaster]], [[Nelumbo|lotus]], [[milkweed]], [[unicorn plant]], and [[wheat]]). [[Ornamental tree]]s and shrubs are often cultivated for their colorful fruits, including [[beautyberry]], [[cotoneaster]], [[holly]], [[pyracantha]], [[skimmia]],  and [[viburnum]].<ref>{{cite book |last=Adams |first=Denise Wiles |title=Restoring American Gardens: An Encyclopedia of Heirloom Ornamental Plants, 1640–1940 |url=https://books.google.com/books?id=J30SOqPLMOEC&pg=PA3&lpg=PA3 |year=2004 |publisher=Timber Press |isbn=978-0-88192-619-4}}</ref>
# * Fruits of [[opium poppy]] are the source of [[opium]], which contains the drugs [[codeine]] and [[morphine]], as well as the biologically inactive chemical theabaine from which the drug [[oxycodone]] is synthesized.<ref>{{cite book |last=Booth |first=Martin |authorlink=Martin Booth |title=Opium: A History |url=https://books.google.com/books?id=kHRyZEQ5rC4C |year=1999 |publisher=St. Martin's Press |isbn=978-0-312-20667-3}}</ref>
# * [[Osage orange]] fruits are used to repel [[cockroach]]es.<ref>{{cite book |last=Cothran |first=James R. |title=Gardens and Historic Plants of the Antebellum South |url=https://books.google.com/books?id=s8OcSmOKeCkC&pg=PA221&lpg=PA221&dq=cockroaches |year=2003 |publisher=University of South Carolina Press |isbn=978-1-57003-501-2 |page=221}}</ref>
# * Many fruits provide [[natural dye]]s (e.g., [[cherry]], [[mulberry]], [[sumac]], and [[walnut]]).<ref>{{cite book |last=Adrosko |first=Rita J. |title=Natural Dyes and Home Dyeing: A Practical Guide with over 150 Recipes |url=https://books.google.com/books?id=EElNckPn0FUC |year=1971 |publisher=Courier Dover Publications |isbn=978-0-486-22688-0}}</ref>
# * Dried [[gourd]]s are used as bird houses, cups, decorations, dishes, musical instruments, and water jugs.
# * [[Pumpkin]]s are carved into [[Jack-o'-lantern]]s for [[Halloween]].
# * The spiny fruit of [[burdock]] or [[cocklebur]] inspired the invention of [[Velcro]].<ref>{{cite book |last=Wake |first=Warren |title=Design Paradigms: A Sourcebook for Creative Visualization |url=https://books.google.com/books?id=j2n1BCqxWjcC&pg=PA162&lpg=PA162 |year=2000 |publisher=John Wiley and Sons |pages=162–63 |isbn=978-0-471-29976-9}}</ref>
# * [[Coir]] fiber from [[coconut]] shells is used for brushes, doormats, floor tiles, insulation, mattresses, sacking, and as a growing medium for container plants. The shell of the coconut fruit is used to make bird houses,  bowls, cups, musical instruments, and souvenir heads.<ref>{{cite web |url= http://www.coconut.com/museum/uses.html |title= The Many Uses of the Coconut |accessdate= 2006-09-14 |publisher= The Coconut Museum |url-status=dead |archiveurl= https://web.archive.org/web/20060906231208/http://www.coconut.com/museum/uses.html |archivedate= 2006-09-06 }}</ref>
# * Fruit is often a subject of [[still life]] paintings.

# == Fruit flies ==
# Fruit flies are species of flies that lay their eggs in the flesh of fruit. The pupae then consume the fruit before maturing into adult flies. Some species lay eggs in fruit that is done maturing or rotten; however, some species select hosts that are not yet ripe. Thus, these fruit flies cause significant damage to fruit crops. An example of this type of fruit fly is the Queensland fruit fly (''[[Bactrocera tryoni|Bactrocera tyroni]]'') ''B. tyroni'' causes more than $28.5 million in damage to Australian fruit crops a year.<ref>{{Cite journal|last=Lloyd|first=Annice C.|last2=Hamacek|first2=Edward L.|last3=Kopittke|first3=Rosemary A.|last4=Peek|first4=Thelma|last5=Wyatt|first5=Pauline M.|last6=Neale|first6=Christine J.|last7=Eelkema|first7=Marianne|last8=Gu|first8=Hainan|date=May 2010|title=Area-wide management of fruit flies (Diptera: Tephritidae) in the Central Burnett district of Queensland, Australia|journal=Crop Protection|volume=29|issue=5|pages=462–469|doi=10.1016/j.cropro.2009.11.003|issn=0261-2194}}</ref> Combating this pest without the use of harmful pesticides is an active area of research.

# == See also ==
# {{Portal|Food}}
# * [[Fruit tree]]
# * [[Fruitarianism]]
# * [[List of culinary fruits]]
# * [[List of foods]]
# * [[List of fruit dishes]]

# == References ==
# {{reflist}}

# == Further reading ==
# * Gollner, Adam J. (2010). ''The Fruit Hunters: A Story of Nature, Adventure, Commerce, and Obsession''. Scribner. {{ISBN|978-0-7432-9695-3}}
# * Watson, R. R., and Preedy, V.R. (2010, eds.). ''Bioactive Foods in Promoting Health: Fruits and Vegetables''. Academic Press. {{ISBN|978-0-12-374628-3}}

# == External links ==
# {{Wikiquote}}
# {{cookbook}}
# {{commons category}}
# {{Wiktionary}}
# * [https://web.archive.org/web/20070218043544/http://www.cas.vanderbilt.edu/bioimages/pages/fruit-devel.htm Images of fruit development from flowers] at bioimages.Vanderbilt.edu
# * [https://web.archive.org/web/20170425010454/http://www.cas.vanderbilt.edu/bioimages/pages/fruit-seed-dispersal.htm Fruit and seed dispersal images] at bioimages.Vanderbilt.edu
# * [http://www.crfg.org/pubs/frtfacts.html Fruit Facts] from California Rare Fruit Growers, Inc.
# * [http://crosstree.info/Documents/Fruit%20ID0.pdf Photo ID of Fruits] by Capt. Pawanexh Kohli
# * {{Cite EB1911|wstitle=Fruit|short=x}}

# {{fruits}}
# {{Botany}}
# {{Agriculture country lists}}
# {{Veganism and vegetarianism}}
# {{Authority control}}

# [[Category:Fruit| ]]
# [[Category:Pollination]]
# """
# # archived_links = extract_links.extract_external_links(revision_text)["archived_links"]
# r = check_if_augmented(live_link, revision_text, {})
# if r:
#     print(r)
#     print("The archived link matches the regular link.")
# else:
#     print("The archived link does not match the regular link.")

"""Search words in each anthem's own language: "sheet music", the instruments, "full score".

Used only in titles, descriptions, headings and alt text (the pages are English), so that a search such as
"partitura de violín Himno Nacional Argentino" finds the violin page. `pattern` puts the instrument word and the
anthem's native title (anthems.py `native[0]`) in the order people type them. An anthem names its language in
LANG_OF (anthem-orchestra slug -> code); English anthems, Khmer, Lao, Mongolian and Maori have none yet.
"""
from __future__ import annotations

INSTRUMENTS = ['violin', 'viola', 'cello', 'double-bass', 'flute', 'piccolo', 'oboe', 'clarinet', 'bassoon', 'horn', 'trumpet', 'trombone', 'tuba', 'timpani', 'percussion', 'harp', 'piano', 'choir']


def _w(sheet, score, orchestra, melody, pattern, inst):
    return dict(sheet=sheet, score=score, orchestra=orchestra, melody=melody, pattern=pattern,
                inst=dict(zip(INSTRUMENTS, inst.split(','))))


WORDS = {
    'es': _w('partitura', 'partitura completa', 'orquesta', 'melodía', 'partitura de {inst} {title}', 'violín,viola,violonchelo,contrabajo,flauta,flautín,oboe,clarinete,fagot,trompa,trompeta,trombón,tuba,timbales,percusión,arpa,piano,coro'),
    'pt': _w('partitura', 'partitura completa', 'orquestra', 'melodia', 'partitura de {inst} {title}', 'violino,viola,violoncelo,contrabaixo,flauta,flautim,oboé,clarinete,fagote,trompa,trompete,trombone,tuba,tímpanos,percussão,harpa,piano,coro'),
    'fr': _w('partition', "partition d'orchestre", 'orchestre', 'mélodie', 'partition {inst} {title}', 'violon,alto,violoncelle,contrebasse,flûte,piccolo,hautbois,clarinette,basson,cor,trompette,trombone,tuba,timbales,percussions,harpe,piano,chœur'),
    'de': _w('Noten', 'Partitur', 'Orchester', 'Melodie', '{title} Noten {inst}', 'Violine,Bratsche,Cello,Kontrabass,Flöte,Piccoloflöte,Oboe,Klarinette,Fagott,Horn,Trompete,Posaune,Tuba,Pauken,Schlagzeug,Harfe,Klavier,Chor'),
    'nl': _w('bladmuziek', 'partituur', 'orkest', 'melodie', '{title} bladmuziek {inst}', 'viool,altviool,cello,contrabas,fluit,piccolo,hobo,klarinet,fagot,hoorn,trompet,trombone,tuba,pauken,slagwerk,harp,piano,koor'),
    'it': _w('spartito', 'partitura', 'orchestra', 'melodia', 'spartito {inst} {title}', 'violino,viola,violoncello,contrabbasso,flauto,ottavino,oboe,clarinetto,fagotto,corno,tromba,trombone,tuba,timpani,percussioni,arpa,pianoforte,coro'),
    'da': _w('noder', 'partitur', 'orkester', 'melodi', '{title} noder {inst}', 'violin,bratsch,cello,kontrabas,fløjte,piccolofløjte,obo,klarinet,fagot,horn,trompet,basun,tuba,pauker,slagtøj,harpe,klaver,kor'),
    'sv': _w('noter', 'partitur', 'orkester', 'melodi', '{title} noter {inst}', 'fiol,altfiol,cello,kontrabas,flöjt,piccolaflöjt,oboe,klarinett,fagott,horn,trumpet,trombon,tuba,pukor,slagverk,harpa,piano,kör'),
    'nb': _w('noter', 'partitur', 'orkester', 'melodi', '{title} noter {inst}', 'fiolin,bratsj,cello,kontrabass,fløyte,pikkolofløyte,obo,klarinett,fagott,horn,trompet,trombone,tuba,pauker,slagverk,harpe,piano,kor'),
    'fi': _w('nuotit', 'partituuri', 'orkesteri', 'melodia', '{title} nuotit {inst}', 'viulu,alttoviulu,sello,kontrabasso,huilu,piccolohuilu,oboe,klarinetti,fagotti,käyrätorvi,trumpetti,pasuuna,tuuba,patarummut,lyömäsoittimet,harppu,piano,kuoro'),
    'pl': _w('nuty', 'partytura', 'orkiestra', 'melodia', '{title} nuty {inst}', 'skrzypce,altówka,wiolonczela,kontrabas,flet,flet piccolo,obój,klarnet,fagot,waltornia,trąbka,puzon,tuba,kotły,perkusja,harfa,fortepian,chór'),
    'ro': _w('partitură', 'partitură completă', 'orchestră', 'melodie', 'partitură {inst} {title}', 'vioară,violă,violoncel,contrabas,flaut,piculină,oboi,clarinet,fagot,corn,trompetă,trombon,tubă,timpane,percuție,harpă,pian,cor'),
    'tr': _w('nota', 'partisyon', 'orkestra', 'melodi', '{title} {inst} notası', 'keman,viyola,viyolonsel,kontrbas,flüt,pikolo,obua,klarnet,fagot,korno,trompet,trombon,tuba,timpani,perküsyon,arp,piyano,koro'),
    'el': _w('παρτιτούρα', 'πλήρης παρτιτούρα', 'ορχήστρα', 'μελωδία', 'παρτιτούρα {inst} {title}', 'βιολί,βιόλα,τσέλο,κοντραμπάσο,φλάουτο,πίκολο,όμποε,κλαρινέτο,φαγκότο,κόρνο,τρομπέτα,τρομπόνι,τούμπα,τύμπανα,κρουστά,άρπα,πιάνο,χορωδία'),
    'uk': _w('ноти', 'партитура', 'оркестр', 'мелодія', '{title} ноти {inst}', 'скрипка,альт,віолончель,контрабас,флейта,флейта-пікколо,гобой,кларнет,фагот,валторна,труба,тромбон,туба,литаври,ударні,арфа,фортепіано,хор'),
    'ar': _w('نوتة موسيقية', 'نوتة الأوركسترا', 'أوركسترا', 'لحن', 'نوتة {inst} {title}', 'كمان,فيولا,تشيلو,كونترباص,فلوت,بيكولو,أوبوا,كلارينيت,باصون,هورن,ترومبيت,ترومبون,توبا,تيمباني,إيقاع,هارب,بيانو,كورال'),
    'fa': _w('نت', 'پارتیتور', 'ارکستر', 'ملودی', 'نت {inst} {title}', 'ویولن,ویولا,ویولنسل,کنترباس,فلوت,پیکولو,ابوا,کلارینت,فاگوت,هورن,ترومپت,ترومبون,توبا,تیمپانی,پرکاشن,چنگ,پیانو,کُر'),
    'zh-Hans': _w('乐谱', '总谱', '管弦乐', '旋律', '{title}{inst}谱', '小提琴,中提琴,大提琴,低音提琴,长笛,短笛,双簧管,单簧管,大管,圆号,小号,长号,大号,定音鼓,打击乐,竖琴,钢琴,合唱'),
    'zh-Hant': _w('樂譜', '總譜', '管弦樂', '旋律', '{title}{inst}譜', '小提琴,中提琴,大提琴,低音提琴,長笛,短笛,雙簧管,單簧管,低音管,法國號,小號,長號,低音號,定音鼓,打擊樂,豎琴,鋼琴,合唱'),
    'ja': _w('楽譜', 'スコア', 'オーケストラ', 'メロディー', '{title} {inst} 楽譜', 'バイオリン,ビオラ,チェロ,コントラバス,フルート,ピッコロ,オーボエ,クラリネット,ファゴット,ホルン,トランペット,トロンボーン,チューバ,ティンパニ,打楽器,ハープ,ピアノ,合唱'),
    'ko': _w('악보', '총보', '오케스트라', '멜로디', '{title} {inst} 악보', '바이올린,비올라,첼로,콘트라베이스,플루트,피콜로,오보에,클라리넷,바순,호른,트럼펫,트롬본,튜바,팀파니,타악기,하프,피아노,합창'),
    'th': _w('โน้ตเพลง', 'สกอร์', 'ออร์เคสตรา', 'ทำนอง', 'โน้ต{inst} {title}', 'ไวโอลิน,วิโอลา,เชลโล,ดับเบิลเบส,ฟลูต,พิคโคโล,โอโบ,คลาริเน็ต,บาสซูน,ฮอร์น,ทรัมเป็ต,ทรอมโบน,ทูบา,ทิมปานี,เครื่องกระทบ,ฮาร์ป,เปียโน,คณะนักร้องประสานเสียง'),
    'vi': _w('bản nhạc', 'tổng phổ', 'dàn nhạc', 'giai điệu', 'bản nhạc {inst} {title}', 'violin,viola,cello,contrabass,sáo flute,piccolo,oboe,clarinet,bassoon,kèn horn,kèn trumpet,kèn trombone,kèn tuba,trống timpani,bộ gõ,đàn hạc,piano,hợp xướng'),
    'ms': _w('not muzik', 'skor penuh', 'orkestra', 'melodi', 'not muzik {inst} {title}', 'biola,viola,selo,dabal bes,flut,pikolo,obo,klarinet,basun,hon,trompet,trombon,tuba,timpani,perkusi,hap,piano,koir'),
    'fil': _w('nota', 'iskor', 'orkestra', 'melodiya', 'nota ng {inst} {title}', 'biyolin,biyola,cello,double bass,plawta,piccolo,oboe,klarinete,bassoon,horn,trumpeta,trombon,tuba,timpani,perkusyon,alpa,piyano,koro'),
    'hi': _w('नोट्स', 'स्कोर', 'ऑर्केस्ट्रा', 'धुन', '{title} {inst} नोट्स', 'वायलिन,वियोला,चेलो,डबल बास,बांसुरी,पिकोलो,ओबो,क्लैरिनेट,बैसून,हॉर्न,ट्रम्पेट,ट्रॉम्बोन,ट्यूबा,टिम्पनी,तालवाद्य,हार्प,पियानो,कोरस'),
    'ga': _w('ceol bileoige', 'scór iomlán', 'ceolfhoireann', 'fonn', '{title} ceol bileoige {inst}', 'veidhlín,vióla,dordveidhil,olldord,feadóg mhór,piccolo,óbó,clairinéid,basún,corn,trumpa,trombón,túba,tiompáin,cnaguirlisí,cláirseach,pianó,cór'),
    'af': _w('bladmusiek', 'volledige partituur', 'orkes', 'melodie', '{title} bladmusiek {inst}', 'viool,altviool,tjello,kontrabas,fluit,piccolo,hobo,klarinet,fagot,horing,trompet,tromboon,tuba,pouke,slagwerk,harp,klavier,koor'),
}

LANG_OF = {'argentina-anthem': 'es', 'colombia-anthem': 'es', 'mexico-anthem': 'es', 'peru-anthem': 'es', 'venezuela-anthem': 'es', 'spain-anthem': 'es', 'brazil-anthem': 'pt', 'portugal-anthem': 'pt', 'france-anthem': 'fr', 'belgium-anthem': 'fr', 'canada-anthem': 'fr', 'germany-anthem': 'de', 'switzerland-anthem': 'de', 'european-union-anthem': 'de', 'netherlands-anthem': 'nl', 'italy-anthem': 'it', 'vatican-anthem': 'it', 'denmark-anthem': 'da', 'sweden-anthem': 'sv', 'norway-anthem': 'nb', 'finland-anthem': 'fi', 'poland-anthem': 'pl', 'romania-anthem': 'ro', 'turkiye-anthem': 'tr', 'greece-anthem': 'el', 'ukraine-anthem': 'uk', 'bahrain-anthem': 'ar', 'qatar-anthem': 'ar', 'saudi-arabia-anthem': 'ar', 'uae-anthem': 'ar', 'iran-anthem': 'fa', 'china-anthem': 'zh-Hans', 'taiwan-anthem': 'zh-Hant', 'japan-anthem': 'ja', 'south-korea-anthem': 'ko', 'north-korea-anthem': 'ko', 'thailand-anthem': 'th', 'vietnam-anthem': 'vi', 'malaysia-anthem': 'ms', 'brunei-anthem': 'ms', 'singapore-anthem': 'ms', 'philippines-anthem': 'fil', 'india-anthem': 'hi', 'ireland-anthem': 'ga', 'south-africa-anthem': 'af'}


def words(slug: str) -> dict | None:
    return WORDS.get(LANG_OF.get(slug, ''))


def native_phrase(slug: str, inst_slug: str | None, title: str) -> str:
    """'partitura de violín Himno Nacional Argentino', or '' when the language has no table."""
    w = words(slug)
    if not w:
        return ''
    if inst_slug is None:
        return f"{w['sheet']} {title}"
    if inst_slug == 'full-score':
        return f"{w['score']} {title} {w['orchestra']}"
    if inst_slug == 'melody':
        return w['pattern'].format(inst=w['melody'], title=title)
    return w['pattern'].format(inst=w['inst'][inst_slug], title=title)

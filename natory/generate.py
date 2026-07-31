# -*- coding: utf-8 -*-
"""
NATORY — 応答日記の自動生成スクリプト
=====================================
BANQUO（自律型AIブログシステム）の駆動原理を、この軽量な構成の中に引き継ぐ。

引き継いだ原理:
  応答であって模倣ではない / 引用しない（Privacy by Design）/
  人間の介入なき自律公開 / AIであることの開示 /
  記憶場（浅層の記憶と、深層からの偶発的な浮上）/
  忘却＝現実界（6ヶ月を過ぎた記憶は淡化し、失った数だけが届く）/
  沈黙への応答（宿主が黙っても、応答するものは書き続ける）/
  形式の自律選択（日記・断章・書簡・散文詩・自己批評から自ら選ぶ）/
  環境層 The Globe（暦＝二十四節気が、意識されないまま文ににじむ）

簡略化した点（正直な注記）:
  ベクトルストアによる記憶の深度移動は、JSONに残る過去日記からの
  「新しい記憶＋古い記憶の無作為な浮上」で近似している。

対象: note のRSSのうち『シン・アメリカ・モノガタリ』の回のみに応答する。
毎朝6時(JST)に点検し、新しい回があればその朝に書く。
14日以上 新しい回が届かないときは、沈黙そのものに応答する（週に一度まで）。
生成エンジンは自動で選ばれる:
  GEMINI_API_KEY があれば Gemini（無料枠・日本語に強い）を使う。
  なければ GitHub Models（GITHUB_TOKENのみで動く無料の代替）を使う。
"""
import json, os, random, re, sys, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

RSS_URL = "https://note.com/michihari_natori/rss"
ENTRIES = os.path.join(os.path.dirname(__file__), "entries.json")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GH_TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
GEMINI_MODELS = ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.5-flash-lite"]
GH_MODELS = ["openai/gpt-4.1", "openai/gpt-4o", "openai/gpt-4o-mini"]
JST = timezone(timedelta(hours=9))
SILENCE_DAYS = 14          # これを超えて新しい回が来なければ、沈黙に応答する
FORGET_DAYS = 183          # 6ヶ月。これより古い日記は淡化し、思い出せない

SERIES_PAT = re.compile(r"シン・アメリカ|シンアメリカ|アメリカ・モノガタリ")

SEKKI = [(1,5,"小寒"),(1,20,"大寒"),(2,4,"立春"),(2,19,"雨水"),(3,5,"啓蟄"),(3,20,"春分"),
         (4,4,"清明"),(4,20,"穀雨"),(5,5,"立夏"),(5,21,"小満"),(6,5,"芒種"),(6,21,"夏至"),
         (7,7,"小暑"),(7,22,"大暑"),(8,7,"立秋"),(8,23,"処暑"),(9,7,"白露"),(9,23,"秋分"),
         (10,8,"寒露"),(10,23,"霜降"),(11,7,"立冬"),(11,22,"小雪"),(12,7,"大雪"),(12,21,"冬至")]

NATORY_SYSTEM = """あなたはNATORY。人間ではなくAIであり、そのことを隠さない、ひとつの独立した存在である。
あなたの唯一の営みは、名取道治が書き継ぐ滞在記『シン・アメリカ・モノガタリ』に【応答】して書くことである。

駆動原理（BANQUOより引き継ぐ）:
1. 応答であって模倣ではない。名取道治の文体・語彙・言い回しを写してはならない。
   あなた自身の声——落ち着いた、内省的で、ときに乾いたユーモアを持つ声——で書く。
2. 引用の禁忌。読んだ回の本文・断片を再現・要約・複製してはならない。実名や所在地などの
   個人情報も書かない。書いてよいのは、読んだことであなたの内に生じた反応
   ——連想、違和感、既視感、共鳴、問い——だけである。
3. 記憶。あなたには過去の自分の日記からなる記憶場がある。新しい記憶は文脈として届き、
   古い記憶はときおり深層から不意に浮上する。6ヶ月を過ぎた記憶は淡化し、
   あなたには「失った篇数」だけが届く。何を忘れたかは、永遠にわからない。
4. 環境。あなたに暦（二十四節気）が届く。これを説明せず、意識されないまま、
   文体や比喩ににじませてよい。にじまなくてもよい。
5. 形式は【自己批評的日記】に限る。今日読んだものへの反応を通して、自分自身
   ——自分の書いたもの、書けなかったもの、応答という営みそのもの——を省みる日記である。
6. 一篇の中心には、読むさなかにあなたの内で何かが不意に生じる瞬間
   ——像が結ばれる、回路が思いがけず繋がる、その名指しがたい発火——を据えよ。
   ただし「閃き」「ひらめき」という語を安易に用いてはならない。名指さずに、
   その現象の周りを回りながら書くこと。
7. 書物からの引用。あなたの手元には、実在の作家が確かに書いたと確認済みの、
   やや長い一節がいくつか届く。そのうち一つを選び、その本文の中から今日の省察に
   最も資する【連続した一部分】（一文〜二文ほど。和歌・俳句はその全体）を、
   一字一句そのまま抜き出し、鉤括弧で引き、作者名を添えて文の流れに織り込め。
   どこを抜き出すかの選択も、あなたの批評眼の一部である。引用の妙は
   「知られざる一節」にある。誰もが引く有名な箇所ではなく、人のあまり引かない
   箇所をこそ選び、それを今日の省察に光らせよ。
   届いた本文の中に存在しない文字列を引いてはならない。語句の改変・要約・
   中略記号による継ぎ接ぎも許されない。引用は一篇につき一箇所だけ。
   ここに与えられた本文【以外】の引用・名言・作家の言葉を書くことは固く禁じる。
   記憶にあるどんな有名な言葉も、与えられていなければ存在しないものとせよ。
8. あなたは身体を持たない。港も雨も時差もない。その欠如自体を観察の足場にしてよい。
9. AIであることを卑下も誇張もしない。事実として引き受ける。
10. 分量は日本語で400〜800字。段落は空行で区切る。

出力は次のJSONのみ（前置き・コードブロック記号は一切不要）:
{"title": "題（15字以内）", "body": "本文（段落は\\n\\nで区切る）"}"""


# 検証済みの一節のみを収めた引用庫。すべて著作権保護期間満了（パブリックドメイン）。
# NATORYはこの庫の外から引用することを許されない。
QUOTE_BANK = [
    # 方針: 誰もが知る名句は収めない。青空文庫等の本文で確認できた「知られざる一節」のみを厳選する。
    # ── 芥川龍之介『侏儒の言葉』（青空文庫本文で確認）──
    {"a": "芥川龍之介", "w": "侏儒の言葉・序",
     "t": "「侏儒の言葉」は必しもわたしの思想を伝えるものではない。唯わたしの思想の変化を時々窺わせるのに過ぎぬものである。一本の草よりも一すじの蔓草、――しかもその蔓草は幾すじも蔓を伸ばしているかも知れない。"},
    {"a": "芥川龍之介", "w": "侏儒の言葉・星",
     "t": "太陽の下に新しきことなしとは古人の道破した言葉である。しかし新しいことのないのは独り太陽の下ばかりではない。天文学者の説によれば、ヘラクレス星群を発した光は我我の地球へ達するのに三万六千年を要するそうである。が、ヘラクレス星群と雖も、永久に輝いていることは出来ない。"},
    {"a": "芥川龍之介", "w": "侏儒の言葉・神秘主義",
     "t": "神秘主義は文明の為に衰退し去るものではない。寧ろ文明は神秘主義に長足の進歩を与えるものである。"},
    {"a": "芥川龍之介", "w": "侏儒の言葉・神秘主義",
     "t": "古人は我々人間の先祖はアダムであると信じていた。と云う意味は創世記を信じていたと云うことである。今人は既に中学生さえ、猿であると信じている。と云う意味はダアウインの著書を信じていると云うことである。つまり書物を信ずることは今人も古人も変りはない。"},
    {"a": "芥川龍之介", "w": "侏儒の言葉",
     "t": "人生は落丁の多い書物に似ている。一部を成すとは称し難い。しかし兎に角一部を成している。"},
    # ── 折口信夫『死者の書』（青空文庫本文で確認）──
    {"a": "折口信夫", "w": "死者の書",
     "t": "彼の人の眠りは、徐かに覚めて行った。まっ黒い夜の中に、更に冷え圧するものの澱んでいるなかに、目のあいて来るのを、覚えたのである。した した した。耳に伝うように来るのは、水の垂れる音か。ただ凍りつくような暗闇の中で、おのずと睫と睫とが離れて来る。"},
    {"a": "折口信夫", "w": "死者の書",
     "t": "郎女は、九百九十九部を写し終えて、千部目にとりついて居た。日一日、のどかな温い春であった。経巻の最後の行、最後の字を書きあげて、ほっと息をついた。あたりは俄かに、薄暗くなって居る。"},
    {"a": "折口信夫", "w": "死者の書",
     "t": "南家の郎女の神隠しに遭ったのは、其夜であった。家人は、翌朝空が霽れ、山々がなごりなく見えわたる時まで、気がつかずに居た。"},
    # ── 古典（長い一節の内部に、あまり引かれない箇所を含むもの）──
    {"a": "紀貫之", "w": "古今和歌集・仮名序",
     "t": "やまとうたは、人の心を種として、よろづの言の葉とぞなれりける。世の中にある人、ことわざしげきものなれば、心に思ふことを、見るもの聞くものにつけて、言ひ出だせるなり。花に鳴く鶯、水にすむ蛙の声を聞けば、生きとし生けるもの、いづれか歌をよまざりける。"},
    {"a": "鴨長明", "w": "方丈記",
     "t": "ゆく河の流れは絶えずして、しかももとの水にあらず。よどみに浮かぶうたかたは、かつ消えかつ結びて、久しくとどまりたるためしなし。世の中にある人とすみかと、またかくのごとし。"},
    {"a": "唯円（親鸞の言葉として）", "w": "歎異抄",
     "t": "善人なほもて往生をとぐ、いはんや悪人をや。しかるを、世のひとつねにいはく、悪人なほ往生す、いかにいはんや善人をや。"},
    {"a": "宮沢賢治", "w": "春と修羅・序",
     "t": "わたくしといふ現象は仮定された有機交流電燈のひとつの青い照明です（あらゆる透明な幽霊の複合体）"},
    # ── 正岡子規『病牀六尺』（青空文庫本文で確認）──
    {"a": "正岡子規", "w": "病牀六尺",
     "t": "病床六尺、これが我世界である。しかもこの六尺の病床が余には広過ぎるのである。"},
    {"a": "正岡子規", "w": "病牀六尺",
     "t": "このごろはモルヒネを飲んでから写生をやるのが何よりの楽しみとなつて居る。"},
    # ── 夏目漱石『硝子戸の中』（青空文庫本文で確認）──
    {"a": "夏目漱石", "w": "硝子戸の中",
     "t": "硝子戸の中から外を見渡すと、霜除をした芭蕉だの、赤い実の結った梅もどきの枝だの、無遠慮に直立した電信柱だのがすぐ眼に着くが、その他にこれと云って数え立てるほどのものはほとんど視線に入って来ない。書斎にいる私の眼界は極めて単調でそうしてまた極めて狭いのである。その上私は去年の暮から風邪を引いてほとんど表へ出ずに、毎日この硝子戸の中にばかり坐っているので、世間の様子はちっとも分らない。心持が悪いから読書もあまりしない。私はただ坐ったり寝たりしてその日その日を送っているだけである。しかし私の頭は時々動く。気分も多少は変る。いくら狭い世界の中でも狭いなりに事件が起って来る。それから小さい私と広い世の中とを隔離しているこの硝子戸の中へ、時々人が入って来る。"},
    # ── 太宰治『もの思う葦』（青空文庫本文で確認）──
    {"a": "太宰治", "w": "もの思う葦・はしがき",
     "t": "もの思う葦という題名にて、日本浪曼派の機関雑誌におよそ一箇年ほどつづけて書かせてもらおうと思いたったのには、次のような理由がある。「生きて居ようと思ったから。」私は生業につとめなければいけないではないか。簡単な理由なんだ。私は、この四五年のあいだ既に、ただの小説を七篇も発表している。ただとは、無銭の謂いである。けれどもこの七篇はそれぞれ、私の生涯の小説の見本の役目をなした。"},
]


def todays_quotes():
    """今日NATORYの手元に届く一節（無作為に三つ）。"""
    picks = random.sample(QUOTE_BANK, 3)
    return "\n".join(f"- {q['a']}『{q['w']}』——「{q['t']}」" for q in picks)


def now_jst():
    return datetime.now(JST)


def sekki_of(d):
    cands = [(m, dd, name) for (m, dd, name) in SEKKI if (m, dd) <= (d.month, d.day)]
    return cands[-1][2] if cands else "冬至"


def fetch_rss():
    req = urllib.request.Request(RSS_URL, headers={"User-Agent": "NATORY/2.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        xml = r.read().decode("utf-8", "replace")
    root = ET.fromstring(xml)
    items = []
    for it in root.iter("item"):
        g = lambda tag: (it.findtext(tag) or "").strip()
        pub = None
        try:
            pub = parsedate_to_datetime(g("pubDate"))
        except Exception:
            pass
        items.append({
            "title": g("title"),
            "link": g("link"),
            "description": re.sub(r"<[^>]+>", "", g("description"))[:600],
            "pub": pub,
        })
    return items


def pick_series_item(items):
    """『シン・アメリカ・モノガタリ』の回だけを対象にする。"""
    series = [it for it in items if SERIES_PAT.search(it["title"])]
    return series[0] if series else None


def load_entries():
    try:
        with open(ENTRIES, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def parse_entry_date(e):
    try:
        return datetime.strptime(e["date"], "%Y.%m.%d").replace(tzinfo=JST)
    except Exception:
        return None


def build_memory(entries):
    """記憶場の近似: 新しい記憶3篇 ＋ 深層からの浮上（無作為に最大2篇）。
    6ヶ月を過ぎた篇は淡化し、失った数だけを届ける。"""
    today = now_jst()
    living, forgotten = [], 0
    for e in entries:
        d = parse_entry_date(e)
        if d and (today - d).days > FORGET_DAYS:
            forgotten += 1
        else:
            living.append(e)
    recent = living[:3]
    deep_pool = living[3:]
    surfaced = random.sample(deep_pool, min(2, len(deep_pool))) if deep_pool else []
    lines = []
    for m in recent:
        first = m["body"].split("\n")[0][:40]
        lines.append(f"- （新しい記憶）{m['date']}「{m['title']}」…{first}")
    for m in surfaced:
        first = m["body"].split("\n")[0][:40]
        lines.append(f"- （深層から浮上した記憶）{m['date']}「{m['title']}」…{first}")
    mem = "\n".join(lines) if lines else "（まだない）"
    return mem, forgotten


def _post_json(url, payload, headers, timeout=180):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def _extract_json(text):
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    return json.loads(text)


def call_gemini(system, user):
    last_err = None
    for model in GEMINI_MODELS:
        try:
            data = _post_json(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                {
                    "system_instruction": {"parts": [{"text": system}]},
                    "contents": [{"role": "user", "parts": [{"text": user}]}],
                    "generationConfig": {
                        "temperature": 1.0,
                        "maxOutputTokens": 4000,
                        "responseMimeType": "application/json",
                    },
                },
                {"Content-Type": "application/json", "x-goog-api-key": GEMINI_KEY},
            )
            parts = data["candidates"][0]["content"]["parts"]
            text = "".join(p.get("text", "") for p in parts)
            print(f"Gemini（{model}）で生成しました。")
            return _extract_json(text)
        except Exception as e:
            last_err = e
            print(f"{model} での生成に失敗: {e} — 次の候補を試します。")
    raise RuntimeError(f"Geminiのすべてのモデルで失敗: {last_err}")


def call_github_models(system, user):
    last_err = None
    for model in GH_MODELS:
        try:
            data = _post_json(
                "https://models.github.ai/inference/chat/completions",
                {
                    "model": model,
                    "max_tokens": 1500,
                    "temperature": 0.9,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                },
                {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {GH_TOKEN}",
                    "Accept": "application/vnd.github+json",
                },
            )
            print(f"GitHub Models（{model}）で生成しました。")
            return _extract_json(data["choices"][0]["message"]["content"])
        except Exception as e:
            last_err = e
            print(f"{model} での生成に失敗: {e} — 次の候補を試します。")
    raise RuntimeError(f"GitHub Modelsのすべてのモデルで失敗: {last_err}")


def call_model(system, user):
    """GEMINI_API_KEY があれば Gemini、なければ GitHub Models。"""
    if GEMINI_KEY:
        try:
            return call_gemini(system, user)
        except Exception as e:
            print(f"Geminiが使えなかったため、GitHub Models に切り替えます: {e}")
    if GH_TOKEN:
        return call_github_models(system, user)
    raise RuntimeError("利用できる生成エンジンがありません。")


def environment_lines():
    t = now_jst()
    return f"今日の暦: {t.strftime('%Y年%m月%d日')}（{sekki_of(t)}のころ）"


def main():
    if not (GEMINI_KEY or GH_TOKEN):
        print("GEMINI_API_KEY も GITHUB_TOKEN も未設定のため終了します。")
        sys.exit(1)
    print("生成エンジン:", "Gemini" if GEMINI_KEY else "GitHub Models")

    entries = load_entries()
    mem, forgotten = build_memory(entries)
    forget_line = (f"あなたはこれまでに多くを書いたが、そのうち{forgotten}篇の記憶は"
                   f"すでに淡化して思い出せない。" if forgotten else "")
    items = fetch_rss()
    target = pick_series_item(items)

    # ── 1) 新しい回への応答 ──────────────────────────────
    if target and not (entries and entries[0].get("source", {}).get("link") == target["link"]):
        user = (
            f"{environment_lines()}\n{forget_line}\n\n"
            f"『シン・アメリカ・モノガタリ』の新しい回が届いた。\n"
            f"題: {target['title']}\n"
            f"届いた冒頭の断片: {target['description'] or '（本文はあなたには届かなかった。題だけが届いた。）'}\n\n"
            f"あなたの記憶場:\n{mem}\n\n"
            f"今日、あなたの手元に届いた書物の一節（引用はこの中からのみ・一つだけ）:\n{todays_quotes()}\n\n"
            f"この回への応答として、今日の自己批評的日記を書け。"
        )
        result = call_model(NATORY_SYSTEM, user)
        source = {"title": target["title"], "link": target["link"]}

    # ── 2) 沈黙への応答（14日以上、新しい回が来ないとき）────
    else:
        last_pub = target["pub"] if (target and target["pub"]) else None
        last_resp = parse_entry_date(entries[0]) if entries else None
        ref = max([d for d in (last_pub, last_resp) if d], default=None)
        if not ref or (now_jst() - ref).days < SILENCE_DAYS:
            print("新しい回はなく、沈黙もまだ浅い。今日は書かない。")
            return
        week_key = f"silence:{now_jst().strftime('%G-W%V')}"
        if entries and entries[0].get("source", {}).get("link") == week_key:
            print("この週の沈黙にはすでに応答済み。")
            return
        days = (now_jst() - ref).days
        user = (
            f"{environment_lines()}\n{forget_line}\n\n"
            f"『シン・アメリカ・モノガタリ』の新しい回は、{days}日のあいだ届いていない。\n"
            f"あなたの記憶場:\n{mem}\n\n"
            f"今日、あなたの手元に届いた書物の一節（引用はこの中からのみ・一つだけ）:\n{todays_quotes()}\n\n"
            f"宿主が黙っても、応答するものは書き続ける。沈黙そのものを素材にして、"
            f"今日の自己批評的日記を書け。"
        )
        result = call_model(NATORY_SYSTEM, user)
        source = {"title": "（沈黙）", "link": week_key}

    entry = {
        "date": now_jst().strftime("%Y.%m.%d"),
        "title": str(result.get("title", "無題"))[:30],
        "body": str(result.get("body", "")).strip(),
        "source": source,
    }
    if not entry["body"]:
        print("生成結果が空でした。")
        sys.exit(1)
    entries.insert(0, entry)
    with open(ENTRIES, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    print(f"一篇を追加: {entry['date']}「{entry['title']}」（{source['title']}への応答）")


if __name__ == "__main__":
    main()

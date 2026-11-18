import os

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
OUT = os.path.join(HERE, "Pixel_Isle_INT4096.html")

SKILL = r"C:\Users\Percy\OneDrive\Desktop\Job record\Classroom\LingLam_3D\.opencode\skills\frontend-slides\plugins\frontend-slides\skills\frontend-slides"
BASE_CSS = open(os.path.join(SKILL, "viewport-base.css"), encoding="utf-8").read()

TOTAL = 27

PAGE = [1]


def head(chapter, title, icon, size=60):
    return f"""
      <div class="slide-head">
        <div class="eyebrow">{chapter}</div>
        <div class="head-row">
          <h2 class="slide-title" style="font-size:{size}px">{title}</h2>
          <img class="head-icon" src="assets/icons/{icon}.png" alt="">
        </div>
        <div class="rule"></div>
      </div>"""


def footer(n):
    return f"""
      <footer class="slide-footer">
        <span>PIXEL ISLE&nbsp;&nbsp;//&nbsp;&nbsp;INT4096&nbsp;&nbsp;//&nbsp;&nbsp;GROUP 2</span>
        <span>2026-27 SEM 1</span>
        <span class="page-chip">{n:02d}</span>
      </footer>"""


def content(body, chapter, title, icon, n, size=60, extra=""):
    PAGE[0] += 1
    return f"""
    <section class="slide content-slide" aria-hidden="true">
      <div class="panel">
        <div class="rivet tl"></div><div class="rivet tr"></div>
        <div class="rivet bl"></div><div class="rivet br"></div>
        {head(chapter, title, icon, size)}
        <div class="slide-body {extra}">
          {body}
        </div>
      </div>
      {footer(PAGE[0])}
    </section>"""


def section(num, title, sub, page):
    PAGE[0] += 1
    return f"""
    <section class="slide section-slide" aria-hidden="true">
      <div class="section-tag">PIXEL ISLE // 001</div>
      <div class="chapter-label">CHAPTER {num} // 04</div>
      <div class="big-number">{num}</div>
      <h2 class="section-title">{title}</h2>
      <div class="section-rule"></div>
      <p class="section-sub">{sub}</p>
      <div class="chapter-progress">
        <span class="{'on' if num == '01' else ''}">01</span>
        <span class="{'on' if num == '02' else ''}">02</span>
        <span class="{'on' if num == '03' else ''}">03</span>
        <span class="{'on' if num == '04' else ''}">04</span>
      </div>
      <div class="wasd">WASD TO ADVANCE</div>
      <div class="spark s1"></div><div class="spark s2"></div><div class="spark s3"></div>
      <footer class="section-footer">
        <span>PIXEL ISLE&nbsp;&nbsp;//&nbsp;&nbsp;INT4096&nbsp;&nbsp;//&nbsp;&nbsp;GROUP 2</span>
        <span class="page-chip">{PAGE[0]:02d}</span>
      </footer>
    </section>"""


def note(t):
    return f'<aside class="notes">{t}</aside>'


def chart_ph(fig, title, text, kind, height, plate_w=720):
    return f"""
      <div class="chart-ph" style="background-image:url('assets/ph_{kind}.png');height:{height}px">
        <div class="fig">{fig}</div>
        <div class="chart-plate" style="width:{plate_w}px">
          <h3>{title}</h3>
          <p>{text}</p>
        </div>
        <div class="drop">DROP CHART HERE</div>
      </div>"""


def chart_img(fig, src, height, caption=""):
    cap = f'<div class="chart-caption">{caption}</div>' if caption else ""
    return f"""
      <div class="chart-ph solid" style="height:{height}px">
        <div class="fig">{fig}</div>
        <img class="chart-pic" src="assets/charts/{src}" alt="{fig}">
      </div>
      {cap}"""


sections = []

# ------------------------------------------------------------------ 1 TITLE
sections.append(f"""
<section class="slide title-slide active" aria-hidden="false">
  <div class="title-panel">
    <div class="rivet tl"></div><div class="rivet tr"></div>
    <div class="rivet bl"></div><div class="rivet br"></div>
    <div class="case-tag">CASE FILE // 001</div>
    <h1 class="game-title"><span class="type">PIXEL ISLE</span></h1>
    <div class="tagline">TURNING TODAY'S NEWS INTO A<br>PLAYABLE DETECTIVE MYSTERY</div>
    <div class="title-rule"></div>
    <p class="title-desc">A classical NLP pipeline that ranks the sentences that matter, then rewrites them as clues in a daily murder mystery.</p>
    <div class="chips">
      <span class="chip">NLP</span>
      <span class="chip">CLASSICAL ML</span>
      <span class="chip">PIXEL GAME</span>
    </div>
    <div class="title-bottom">
      <button class="start-btn" data-next>PRESS START &gt;&gt;</button>
      <div class="course">INT4096&nbsp;&nbsp;ARTIFICIAL INTELLIGENCE &amp;<br>MACHINE LEARNING IN EDUCATION</div>
    </div>
    <div class="title-foot">THE EDUCATION UNIVERSITY OF HONG KONG&nbsp;&nbsp;//&nbsp;&nbsp;2026-27 SEM 1<br>GROUP 2&nbsp;&nbsp;//&nbsp;&nbsp;CHIU WAI YIU · LAI CHUN KUI · LAI WAN YAU SONYA · MAK TSUN WAI MARSIO<br>WONG CHING WAI · WONG SUI KI · WONG TSZ CHING&nbsp;&nbsp;//&nbsp;&nbsp;18 NOV 2026</div>
  </div>
  <div class="room-tag">HOME ROOM // 22:40</div>
  {note("Timing 0:00-1:00. Open with the hook: today's news is usually a wall of text. Pixel Isle turns one real news story into a playable murder mystery. Say the group number and that this is an end-to-end NLP + game project.")}
</section>""")

# ------------------------------------------------------------------ 2 AGENDA
agenda = [
    ("01", "THE PROBLEM", "News is competing with games. Right now, games are winning.", "red", "alert"),
    ("02", "THE GAME", "A browser detective mystery built from today's news.", "gold", "game"),
    ("03", "THE PIPELINE", "Crawl, clean, label, train, rank, rewrite, inject.", "navy", "model"),
    ("04", "THE RESULTS", "Model comparison, limits, and what we learned.", "green", "chart"),
]
rows = "".join(
    f"""<div class="agenda-row reveal" style="--i:{i}">
      <div class="agenda-num {accent}">{num}</div>
      <div class="agenda-copy"><h3>{title}</h3><p>{desc}</p></div>
      <div class="agenda-icon"><img src="assets/icons/{icon}.png" alt=""></div>
    </div>""" for i, (num, title, desc, accent, icon) in enumerate(agenda)
)
sections.append(content(f"""
      <div class="agenda">{rows}</div>
      <div class="agenda-note">4 CHAPTERS&nbsp;&nbsp;//&nbsp;&nbsp;1 PLAYABLE CASE&nbsp;&nbsp;//&nbsp;&nbsp;ZERO WORKSHEETS</div>
      {note("Timing 1:00-1:30. Four chapters: problem, game, pipeline, results. The presentation is 20 minutes. Point at the chapter list rather than reading it.")}
""", "MISSION SELECT // 20 MINUTES", "CHOOSE A CHAPTER", "game", 2, 64))

# ------------------------------------------------------------------ 3 SECTION 01
sections.append(section("01", "THE PROBLEM", "News is competing with games.<br>Right now, games are winning.", 3))
sections[-1] = sections[-1].replace("</section>", note("Timing 1:30-2:00. Chapter break. Move from the product idea to the education problem.") + "</section>")

# ------------------------------------------------------------------ 4 PROBLEM
sections.append(content(f"""
      <div class="stats-grid">
        <div class="stat-card black reveal" style="--i:0">
          <div class="stat-number">78%</div>
          <div class="stat-label">of kids find traditional news boring</div>
          <div class="stat-source">SOURCE: MTM NEWS ALERT, 2024</div>
        </div>
        <div class="stat-card red reveal" style="--i:1">
          <div class="stat-number">27%</div>
          <div class="stat-label">of kids read news during a month in Canada</div>
          <div class="stat-source">SOURCE: MTM NEWS ALERT, 2024</div>
        </div>
      </div>
      <div class="cards-3">
        <div class="mini-card reveal" style="--i:2">
          <div class="bar navy"><span>COMPLEX VOCABULARY</span><img src="assets/icons/book.png" alt=""></div>
          <p>Long sentences and unfamiliar words block the story.</p>
        </div>
        <div class="mini-card reveal" style="--i:3">
          <div class="bar navy"><span>LOW MOTIVATION</span><img src="assets/icons/alert.png" alt=""></div>
          <p>Reading feels like a task, not something you choose.</p>
        </div>
        <div class="mini-card reveal" style="--i:4">
          <div class="bar navy"><span>INFORMATION OVERLOAD</span><img src="assets/icons/chart.png" alt=""></div>
          <p>Too many stories, too little signal about what matters.</p>
        </div>
      </div>
      <div class="source-line">Source: MtM News Alert 09-05-2024 — https://mtm-otm.ca/_files/NewsAlert/09-05-2024.pdf</div>
      {note("Timing 2:00-4:00. Two numbers set up the problem. Then name the three barriers: vocabulary, motivation, overload. The issue is not a lack of news, but a lack of an engaging entry point.")}
""", "CHAPTER 01 // THE PROBLEM", "NEWS FEELS LIKE HOMEWORK", "alert", 4, 60))

# ------------------------------------------------------------------ 5 ANSWER
sections.append(content(f"""
      <div class="answer-grid">
        <div class="goal-list">
          <div class="goal reveal" style="--i:0">
            <div class="goal-icon red"><img src="assets/icons/news.png" alt=""></div>
            <div><h3>READ MORE NEWS</h3><p>A daily reason to open a real story.</p></div>
          </div>
          <div class="goal reveal" style="--i:1">
            <div class="goal-icon gold"><img src="assets/icons/target.png" alt=""></div>
            <div><h3>BUILD INTEREST</h3><p>Curiosity first; comprehension follows.</p></div>
          </div>
          <div class="goal reveal" style="--i:2">
            <div class="goal-icon green"><img src="assets/icons/clue.png" alt=""></div>
            <div><h3>TRAIN CRITICAL THINKING</h3><p>Weigh evidence, then explain the death.</p></div>
          </div>
        </div>
        <div class="flow-list">
          <div class="flow-label">THE TRANSFORMATION</div>
          <div class="flow-card reveal" style="--i:0">
            <div class="flow-icon navy"><img src="assets/icons/news.png" alt=""></div>
            <div><h3>TODAY'S NEWS</h3><p>A real BBC story</p></div>
          </div>
          <div class="flow-arrow">▼</div>
          <div class="flow-card reveal" style="--i:1">
            <div class="flow-icon gold"><img src="assets/icons/model.png" alt=""></div>
            <div><h3>MODEL RANKS</h3><p>Key sentences survive</p></div>
          </div>
          <div class="flow-arrow">▼</div>
          <div class="flow-card reveal" style="--i:2">
            <div class="flow-icon red"><img src="assets/icons/clue.png" alt=""></div>
            <div><h3>5 CLUES</h3><p>Rewritten for the case</p></div>
          </div>
          <div class="flow-arrow">▼</div>
          <div class="flow-card reveal" style="--i:3">
            <div class="flow-icon green"><img src="assets/icons/game.png" alt=""></div>
            <div><h3>PIXEL ISLE</h3><p>A mystery to solve</p></div>
          </div>
        </div>
      </div>
      {note("Timing 4:00-5:00. The design response is not a news app with a quiz. It is a detective game where the news supplies the clues. The goals on the left map directly to the problem slide.")}
""", "CHAPTER 01 // OUR ANSWER", "WHAT IF THE NEWS WAS THE GAME?", "game", 5, 50))

# ------------------------------------------------------------------ 6 SECTION 02
sections.append(section("02", "THE GAME", "A murder mystery you can play<br>in a browser.", 6))
sections[-1] = sections[-1].replace("</section>", note("Timing 5:00-5:20. Chapter break. This is the product demo section: what the player actually sees and does.") + "</section>")

# ------------------------------------------------------------------ 7 GAME DEMO
sections.append(content(f"""
      <div class="game-layout">
        <div>
          <div class="game-frame"><img src="assets/game.png" alt="Pixel Isle home room game screenshot"></div>
          <div class="game-caption">HOME ROOM — the scene where the case begins.</div>
        </div>
        <div class="game-side">
          <div class="control reveal" style="--i:0"><div class="key">WASD</div><div class="action">MOVE</div></div>
          <div class="control reveal" style="--i:1"><div class="key">E</div><div class="action">INSPECT</div></div>
          <div class="control reveal" style="--i:2"><div class="key">1-4</div><div class="action">ANSWER</div></div>
          <div class="note-card case-note reveal" style="--i:3">
            <div class="bar red"><span>THE CASE</span><img src="assets/icons/clue.png" alt=""></div>
            <div class="body">Papers = the day's article.<br>5 objects = 5 MCQs.<br>Finale = explain the death.<br>Score = answers + keywords.</div>
          </div>
          <div class="live-demo">LIVE DEMO &gt;&gt;</div>
        </div>
      </div>
      {note("Timing 5:20-8:00. Live demo slide. If the browser is available, switch to index.html -> Play for 60-90 seconds: walk to an object, press E, show a clue, press 1-4. Emphasise that the content is generated from a real news story.")}
""", "CHAPTER 02 // THE GAME", "INSPECT. COLLECT. ACCUSE.", "game", 7, 60))

# ------------------------------------------------------------------ 8 SECTION 03
sections.append(section("03", "THE PIPELINE", "Real news in.<br>Playable clues out.", 8))
sections[-1] = sections[-1].replace("</section>", note("Timing 8:00-8:20. Chapter break. The next four slides are the technical core.") + "</section>")

# ------------------------------------------------------------------ 9 PIPELINE
steps = [
    ("01", "COLLECT", "30+ RSS feeds", "news", "red"),
    ("02", "CLEAN + SPLIT", "articles -&gt; sentences", "gear", "gold"),
    ("03", "LABEL", "0 filler / 1 key / 2 evidence", "target", "navy"),
    ("04", "TRAIN", "TF-IDF + Logistic Regression", "model", "green"),
    ("05", "RANK", "P(key) for every sentence", "chart", "red"),
    ("06", "REWRITE", "top sentences -&gt; clues", "book", "gold"),
    ("07", "INJECT", "clues -&gt; case_data.js", "gear", "navy"),
    ("08", "PLAY", "inspect, answer, score", "game", "green"),
]
pipe = "".join(
    f"""<div class="pipe-box reveal" style="--i:{i}">
      <div class="num {accent}">{num}</div>
      <img src="assets/icons/{icon}.png" alt="">
      <h3>{title}</h3><p>{sub}</p>
    </div>""" for i, (num, title, sub, icon, accent) in enumerate(steps)
)
sections.append(content(f"""
      <div class="pipe-grid">{pipe}</div>
      <div class="banner reveal">THE MODEL DECIDES WHAT MATTERS. THE GAME MAKES IT MATTER TO THE PLAYER.</div>
      {note("Timing 8:20-10:00. Walk the pipeline left to right, then top to bottom. The key split is step 4: the model ranks sentences. Step 6 is the last mile: raw news sentences are rewritten into clues.")}
""", "CHAPTER 03 // SYSTEM", "FROM RSS TO MURDER SCENE", "gear", 9, 58))

# ------------------------------------------------------------------ 10 DATASET
sections.append(content(f"""
      <div class="dataset-grid">
        <div class="dataset-left">
          <div class="dataset-stats">
            <div class="dataset-stat reveal" style="--i:0"><div class="n">67,647</div><div class="l">labelled sentences</div></div>
            <div class="dataset-stat reveal" style="--i:1"><div class="n">1,322</div><div class="l">news articles</div></div>
            <div class="dataset-stat reveal" style="--i:2"><div class="n">9</div><div class="l">news categories</div></div>
            <div class="dataset-stat reveal" style="--i:3"><div class="n">30+</div><div class="l">RSS feeds</div></div>
          </div>
          <div class="dataset-note">
            <p>Dataset: today's news from BBC, CNN, The Guardian and 30+ public RSS feeds.</p>
            <p class="muted">Article-level split: 80% train / 10% validation / 10% test.</p>
          </div>
        </div>
        <div class="reveal" style="--i:3">
          {chart_img("FIG. 01", "label_distribution.png", 590, "Source: data_full.csv -> sentence_label value_counts()")}
        </div>
      </div>
      {note("Timing 10:00-11:30. Size matters here: 67,647 sentences from 1,322 articles across 9 categories. The right side shows the class distribution; imbalance is a key discussion point.")}
""", "CHAPTER 03 // DATA", "THE CASE FILE: 67,647 SENTENCES", "news", 10, 49))

# ------------------------------------------------------------------ 11 PREPROCESSING
sections.append(content(f"""
      <div class="prep-wrap">
        <div class="prep-cols">
          <div class="prep-col reveal" style="--i:0">
            <div class="prep-bar red">CLEANING</div>
            <ul>
              <li>Strip HTML tags and unescape entities</li>
              <li>Normalize whitespace; trim excessive ellipses</li>
              <li>Drop articles &lt;50 chars, sentences &lt;15</li>
              <li>Split sentences with abbreviation awareness</li>
              <li>Deduplicate articles by content hash</li>
            </ul>
          </div>
          <div class="prep-col reveal" style="--i:1">
            <div class="prep-bar green">FEATURES + SPLIT</div>
            <ul>
              <li>TF-IDF unigrams + bigrams</li>
              <li>min_df=2, sublinear_tf=True</li>
              <li>Sentence position + neighbouring sentences</li>
              <li>Article-level 80 / 10 / 10 split</li>
              <li>class_weight='balanced' for imbalance</li>
            </ul>
          </div>
        </div>
        <div class="why reveal" style="--i:2">WHY IT MATTERS: cleaner sentences mean less TF-IDF noise and a clearer key-sentence signal.</div>
        <div class="example reveal" style="--i:3">
          <div class="example-label">BEFORE / AFTER</div>
          <div class="example-row"><span class="raw">RAW</span><code>&lt;p&gt;Breaking&nbsp;news&nbsp;&amp;nbsp;analysis...&lt;/p&gt;</code></div>
          <div class="example-row"><span class="clean">CLEAN</span><code>Breaking news analysis...</code></div>
        </div>
        <div class="terminal reveal" style="--i:4">
          <div>&gt; raw HTML&nbsp;&nbsp;-&gt;&nbsp;&nbsp;clean sentence&nbsp;&nbsp;-&gt;&nbsp;&nbsp;TF-IDF vector&nbsp;&nbsp;-&gt;&nbsp;&nbsp;label 0 / 1 / 2</div>
          <div class="ok">[OK] 1,322 articles became 67,647 labelled sentences.</div>
        </div>
      </div>
      {note("Timing 11:30-12:30. Two columns: cleaning and representation. Highlight abbreviation-aware splitting, neighbour context, and article-level split. The terminal strip summarises the transformation.")}
""", "CHAPTER 03 // DATA", "CLEAN TEXT IN, USEFUL SIGNALS OUT", "gear", 11, 47))

# ------------------------------------------------------------------ 12 METHOD
sections.append(content(f"""
      <div class="method-wrap">
        <div class="method-q reveal">WHICH SENTENCE CARRIES THE STORY?</div>
        <div class="class-grid">
          <div class="class-card reveal" style="--i:0">
            <div class="class-num muted">0</div>
            <div class="class-copy"><h3>FILLER</h3><p>Stylistic, transitional, optional. Cut it and the story still stands.</p></div>
          </div>
          <div class="class-card reveal" style="--i:1">
            <div class="class-num gold">1</div>
            <div class="class-copy"><h3>KEY</h3><p>Main topic, central events, core facts. This is the story.</p></div>
          </div>
          <div class="class-card reveal" style="--i:2">
            <div class="class-num red">2</div>
            <div class="class-copy"><h3>EVIDENCE</h3><p>Secondary but useful context: quotes, numbers, background.</p></div>
          </div>
        </div>
        <div class="model-banner reveal" style="--i:3">
          <div class="model-title">PRIMARY MODEL: TF-IDF + LOGISTIC REGRESSION</div>
          <div class="model-specs">
            <div><span>VECTORIZER</span><p>unigrams + bigrams<br>min_df=2, sublinear_tf</p></div>
            <div><span>CLASSIFIER</span><p>LogisticRegression<br>balanced, max_iter=2000</p></div>
            <div><span>TARGET</span><p>rank sentences by P(key)<br>for clue selection</p></div>
          </div>
        </div>
      </div>
      {note("Timing 12:30-13:30. The task is three-class sentence classification. Label 1 matters most for clue selection. The primary model is deliberately classical: TF-IDF plus class-weighted logistic regression.")}
""", "CHAPTER 03 // MODEL", "THREE LABELS, ONE QUESTION", "target", 12, 58))

# ------------------------------------------------------------------ 13 WHY
reasons = [
    "Strong, well-established baseline for text classification",
    "Handles high-dimensional sparse data efficiently",
    "Class weights address filler / key / evidence imbalance",
    "Coefficients show which words drive each class",
    "Fast to train, easy to reproduce on CPU",
]
reason_html = "".join(
    f"""<div class="reason reveal" style="--i:{i}"><img src="assets/icons/check.png" alt=""><span>{r}</span></div>"""
    for i, r in enumerate(reasons)
)
sections.append(content(f"""
      <div class="why-grid">
        <div class="why-left">
          {reason_html}
          <div class="also"><span>ALSO COMPARED</span>
            <span class="chip sm">LINEAR SVM</span><span class="chip sm">MULTINOMIAL NB</span><span class="chip sm">RANDOM FOREST</span>
          </div>
        </div>
        <div class="model-card reveal" style="--i:2">
          <h3>MODEL CARD</h3>
          <div class="model-card-rule"></div>
          <dl>
            <dt>FEATURES</dt><dd>TF-IDF, 1-2 grams</dd>
            <dt>MIN_DF</dt><dd>2</dd>
            <dt>SUBLINEAR_TF</dt><dd>True</dd>
            <dt>CLASS_WEIGHT</dt><dd>balanced</dd>
            <dt>MAX_ITER</dt><dd>2000</dd>
            <dt>BASELINE</dt><dd>classical, no deep learning</dd>
          </dl>
          <div class="model-foot">FAST ENOUGH TO RETRAIN DAILY.</div>
        </div>
      </div>
      {note("Timing 13:30-14:30. Justify the model in five points. The strongest are class weighting and interpretability. The model card lists exact settings so the audience can trust reproducibility.")}
""", "CHAPTER 03 // MODEL", "WHY TF-IDF + LOGISTIC REGRESSION", "check", 13, 48))

# ------------------------------------------------------------------ 14 SPLIT
sections.append(content(f"""
      <div class="split-wrap">
        <div class="split-bar reveal">
          <div class="seg train">TRAIN&nbsp;&nbsp;80%</div>
          <div class="seg val">VAL&nbsp;&nbsp;10%</div>
          <div class="seg test">TEST&nbsp;&nbsp;10%</div>
        </div>
        <div class="split-note">ARTICLE-LEVEL SPLIT — no sentence from one article appears in two sets.</div>
        <div class="role-grid">
          <div class="role-card reveal" style="--i:0"><div class="bar gold">TRAIN<img src="assets/icons/book.png" alt=""></div><p>Learn model parameters.</p></div>
          <div class="role-card reveal" style="--i:1"><div class="bar green">VALIDATION<img src="assets/icons/target.png" alt=""></div><p>Check performance during development.</p></div>
          <div class="role-card reveal" style="--i:2"><div class="bar red">TEST<img src="assets/icons/chart.png" alt=""></div><p>Report final performance once.</p></div>
        </div>
        <div class="metric-row">
          <div class="metric-label">SAME METRICS FOR EVERY MODEL</div>
          <span class="metric">MACRO-F1</span><span class="metric">KEY-F1</span><span class="metric">TOP-3</span><span class="metric">TRAIN TIME</span>
          <span class="seed">ONE SEED<br>SEED = 42</span>
        </div>
        <div class="why reveal" style="--i:3">WHY IT MATTERS: article-level splitting stops the model memorising the same story in train and test.</div>
        <div class="split-foot">Hold the split fixed. Report the same metric definitions. Then compare models.</div>
      </div>
      {note("Timing 14:30-15:15. Fair comparison is the message. Every model uses the same article-level split and metric definitions. Train learns, validation checks, test is reported once.")}
""", "CHAPTER 03 // EVALUATION", "A FAIR FIGHT: SAME SPLIT, SAME METRICS", "target", 14, 40))

# ------------------------------------------------------------------ 14b ETHICS & DATA
sections.append(content(f"""
      <div class="prep-wrap">
        <div class="prep-cols">
          <div class="prep-col reveal" style="--i:0">
            <div class="prep-bar red">HOW WE USE NEWS</div>
            <ul>
              <li>One real story per day from public RSS feeds (BBC, CNN, The Guardian).</li>
              <li>Content is current, real-world news — not fabricated.</li>
              <li>We keep short sentence excerpts, not full republished articles.</li>
              <li>Non-commercial, classroom prototype within a university course.</li>
            </ul>
          </div>
          <div class="prep-col reveal" style="--i:1">
            <div class="prep-bar green">COPYRIGHT &amp; LICENSE</div>
            <ul>
              <li>BBC and other outlets are copyrighted, not open-source.</li>
              <li>RSS is for personal reading; brief excerpts are low-risk in a student prototype.</li>
              <li>We do not redistribute full articles or claim ownership.</li>
              <li>Any public demo uses the shortest excerpts and credits the source.</li>
            </ul>
          </div>
        </div>
        <div class="why reveal" style="--i:2">REAL NEWS IS THE INPUT — USED IN GOOD FAITH FOR EDUCATION.</div>
      </div>
      {note("Ethics and data use. The input is real, current news used for a short educational prototype. BBC content is copyrighted, not open-source, so the demo stays non-commercial and credits the source.")}
""", "CHAPTER 03 // ETHICS & DATA", "REAL NEWS, USED RESPONSIBLY", "alert", 15, 46))

# ------------------------------------------------------------------ 15 SECTION 04
sections.append(section("04", "THE RESULTS", "The model ranks.<br>The numbers decide.", 15))
sections[-1] = sections[-1].replace("</section>", note("Timing 15:15-15:30. Chapter break. Now the evidence: comparison table, training curve, confusion matrix.") + "</section>")

# ------------------------------------------------------------------ 16 RESULTS
sections.append(content(f"""
      <table class="pixel-table reveal">
        <thead><tr><th>METHOD</th><th>MACRO-F1</th><th>KEY-F1</th><th>TOP-3</th><th>TIME</th><th>PARAMS</th></tr></thead>
        <tbody>
          <tr><td>TF-IDF + Logistic Regression (baseline)</td><td class="center">0.653</td><td class="center">0.424</td><td class="center">0.455</td><td class="center">&lt;1 min</td><td class="center">0.39M</td></tr>
          <tr><td>LSTM + self-built vocab</td><td class="center">0.709</td><td class="center">0.543</td><td class="center">0.618</td><td class="center">8.5 min</td><td class="center">5.2M</td></tr>
          <tr><td>LSTM + RoBERTa tokenizer</td><td class="center">0.736</td><td class="center">0.552</td><td class="center">0.638</td><td class="center">7.8 min</td><td class="center">6.7M</td></tr>
          <tr class="best"><td>&gt;&gt; DistilRoBERTa (reference)</td><td class="center">0.806</td><td class="center">0.673</td><td class="center">0.693</td><td class="center">21 min</td><td class="center">82.1M</td></tr>
        </tbody>
      </table>
      <div class="results-chart reveal" style="--i:3">
        {chart_img("FIG. 02", "compare_wide.png", 330, "")}
      </div>
      <div class="source-line">Primary course model: TF-IDF + LogReg (baseline). Neural rows are reference comparisons (seed 42).</div>
      {note("Timing 15:30-17:00. The table is the evidence. DistilRoBERTa leads every reported metric, at 82.1M parameters and 21 minutes. The TF-IDF baseline is included as the primary classical model.")}
""", "CHAPTER 04 // RESULTS", "MODEL COMPARISON: THE NUMBERS", "chart", 16, 53))

# ------------------------------------------------------------------ 17 TRAINING CURVE
sections.append(content(f"""
      {chart_img("FIG. 03", "training_progress.png", 620, "Train / val loss + validation macro-F1 by epoch (LSTM word · LSTM tok · DistilRoBERTa).")}
      <div class="why reveal" style="--i:1">READ THE CURVE: training loss falls, validation loss wobbles, and validation macro-F1 rises overall. Lower training loss is not always better — keep the best validation checkpoint.</div>
      {note("Timing 17:00-17:45. Show the real training curves. Validation loss fluctuates while validation F1 rises; we keep the best validation checkpoint.")}
""", "CHAPTER 04 // RESULTS", "TRAINING CURVE: WHAT TO WATCH", "chart", 17, 53))

# ------------------------------------------------------------------ 18 ERROR
sections.append(content(f"""
      <div class="double-grid wide-left">
        <div class="reveal" style="--i:0">
          {chart_img("FIG. 04", "confusion_matrix.png", 620, "Test-set matrix — TF-IDF + Logistic Regression")}
        </div>
        <div class="side-card reveal" style="--i:1">
          <div class="bar red">ERROR ANALYSIS</div>
          <ul>
            <li><b>Key sentences are hardest.</b> They are rare and sit between filler and evidence, so they are easy to confuse.</li>
            <li><b>Labels are noisy.</b> DeepSeek-assisted labels can be wrong, so scores absorb label error.</li>
            <li><b>Class imbalance.</b> Filler dominates; balanced weights help, but do not erase the problem.</li>
            <li><b>Next step.</b> Inspect top false positives and false negatives, then refine the label guide.</li>
          </ul>
          <div class="side-note">NEXT: INSPECT 20 ERRORS -&gt; UPDATE LABEL GUIDE</div>
          <div class="side-strip">LABEL NOISE = SCORE NOISE</div>
        </div>
      </div>
      {note("Timing 17:45-18:30. The matrix shows the test-set result. Key sentences are the hardest class. Labels were LLM-assisted, so label noise is a real limitation. End with concrete error inspection.")}
""", "CHAPTER 04 // RESULTS", "WHERE THE MODEL STILL STRUGGLES", "alert", 18, 48))

# ------------------------------------------------------------------ 19 RESULTS SHOW
sections.append(content(f"""
      <div class="results-grid">
        <div class="result-card reveal" style="--i:0"><div class="bar green">BEST REPORTED<img src="assets/icons/check.png" alt=""></div><p>DistilRoBERTa: 0.806 macro-F1 and 0.673 key-F1.</p></div>
        <div class="result-card reveal" style="--i:1"><div class="bar gold">BIGGER MODEL<img src="assets/icons/model.png" alt=""></div><p>82.1M parameters vs 5.2M / 6.7M for the LSTM runs.</p></div>
        <div class="result-card reveal" style="--i:2"><div class="bar red">NOISY LABELS<img src="assets/icons/alert.png" alt=""></div><p>DeepSeek-assisted labels may contain errors that move scores.</p></div>
        <div class="result-card reveal" style="--i:3"><div class="bar navy">ONE SEED<img src="assets/icons/target.png" alt=""></div><p>Single seed; measures sentence classification, not learning gains.</p></div>
      </div>
      <div class="banner reveal">USEFUL FOR RANKING KEY SENTENCES. NOT A SUBSTITUTE FOR TEACHER JUDGEMENT.</div>
      {note("Timing 18:30-19:00. Four honest takeaways. The best number belongs to a larger reference model. Labels are noisy. One seed is not a stability study. It measures sentence classification, not learning gains.")}
""", "CHAPTER 04 // RESULTS", "WHAT THE RESULTS SHOW", "target", 19, 56, "center-body"))

# ------------------------------------------------------------------ 20 IMPLICATIONS
impact = [
    ("01", "EXTRACT", "The game pulls key sentences from a real BBC story.", "news"),
    ("02", "CLASSIFY", "The model ranks importance: filler, key, evidence.", "model"),
    ("03", "UNDERSTAND", "Kids meet the story one clue at a time.", "book"),
    ("04", "WANT MORE", "Current affairs becomes something to play.", "game"),
]
impact_html = "".join(
    f"""<div class="impact-card reveal" style="--i:{i}"><div class="impact-num">{num}</div><img src="assets/icons/{icon}.png" alt=""><h3>{title}</h3><p>{body}</p></div>"""
    for i, (num, title, body, icon) in enumerate(impact)
)
sections.append(content(f"""
      <div class="impact-grid">{impact_html}</div>
      <div class="impact-bottom">
        <div class="impact-big red reveal"><span>THE PROBLEM</span><p>Bored by news.&nbsp; Rarely reads it.</p></div>
        <div class="impact-big green reveal"><span>THE SHIFT</span><p>Curious.&nbsp; Plays the story daily.</p></div>
      </div>
      <div class="impact-line">FROM 'I DON'T READ THE NEWS' TO 'I SOLVED TODAY'S CASE.'</div>
      {note("Timing 19:00-19:30. Tie the pipeline back to the problem. The model extracts and ranks; the game turns ranking into pacing and participation. Do not overclaim learning gains.")}
""", "CHAPTER 04 // IMPLICATIONS", "SO WHAT? PROBLEM -&gt; RESULT", "game", 20, 54))

# ------------------------------------------------------------------ 21 CHALLENGES
challenges = [
    ("1", "LARGE-SCALE LABELLING", "67,647 sentences. 'Important' is hard to define. LLM-assisted labels brought noise and imbalance.", "red"),
    ("2", "COURSE VS PERFORMANCE", "The course focuses on classical ML. The best scores came from DistilRoBERTa, so lighter models were also trained for a fair comparison.", "gold"),
    ("3", "MODEL OUTPUT -&gt; CLUES", "Raw news sentences do not fit a murder mystery. A rewrite step is needed; early clues broke immersion.", "navy"),
    ("4", "ENGINEERING + REPRO", "Crawler, labelling, training, Streamlit and the game had to work together. RSS changes broke the pipeline.", "green"),
]
ch_html = "".join(
    f"""<div class="challenge reveal" style="--i:{i}"><div class="challenge-num {accent}">{num}</div><div><h3>{title}</h3><p>{body}</p></div></div>"""
    for i, (num, title, body, accent) in enumerate(challenges)
)
sections.append(content(f"""
      <div class="challenge-grid">{ch_html}</div>
      <div class="challenge-line">EVERY CHALLENGE CHANGED THE PIPELINE, NOT JUST THE MODEL.</div>
      {note("Timing 19:30-20:00. Four challenges. The big one is labelling. The second is the classical-ML restriction versus stronger reference models. The third is the last mile, and the fourth is reproducibility.")}
""", "CHAPTER 04 // REFLECTION", "CHALLENGES FACED", "alert", 21, 60, "center-body"))

# ------------------------------------------------------------------ 22 LEARNINGS
learn = [
    "Pipeline quality beats any single model.",
    "Report both stronger and lighter models.",
    "NLP output must be adapted to the target domain.",
    "Fixed seed + identical splits = fair comparison.",
    "Clear interfaces prevent integration pain.",
    "The last mile is hardest: predictions -&gt; usable clues.",
]
learn_html = "".join(
    f"""<div class="learn reveal" style="--i:{i}"><div class="learn-num">{i+1}</div><p>{item}</p></div>"""
    for i, item in enumerate(learn)
)
sections.append(content(f"""
      <div class="learn-grid">{learn_html}</div>
      <div class="banner reveal">SHIP THE WHOLE PIPELINE, NOT JUST THE MODEL.</div>
      {note("Timing 20:00-20:30 if time allows. Six learnings. The final line is the thesis: an education AI system succeeds or fails on the whole pipeline, especially the last mile.")}
""", "CHAPTER 04 // REFLECTION", "WHAT THE TEAM LEARNED", "book", 22, 60, "center-body"))

# ------------------------------------------------------------------ 22b LIMITATIONS & FUTURE
sections.append(content(f"""
      <div class="prep-wrap">
        <div class="prep-cols">
          <div class="prep-col reveal" style="--i:0">
            <div class="prep-bar red">LIMITATIONS (HONEST)</div>
            <ul>
              <li>Single seed (42) — no stability study yet.</li>
              <li>LLM-assisted labels introduce noise.</li>
              <li>Scores measure sentence importance, not learning gains.</li>
            </ul>
          </div>
          <div class="prep-col reveal" style="--i:1">
            <div class="prep-bar green">FUTURE WORK</div>
            <ul>
              <li>Make the clues more directly related to the story.</li>
              <li>Add student history and daily streaks for engagement.</li>
              <li>Sharpen the news-to-clue mapping (currently not fully focused).</li>
            </ul>
          </div>
        </div>
        <div class="why reveal" style="--i:2">NEXT ITERATION: THE NEWS SHOULD BE THE MYSTERY, NOT JUST THE BACKDROP.</div>
      </div>
      {note("Limitations and next steps. Honest limits: one seed, noisy labels, and the metric measures sentence importance not learning. Future work: tie clues closer to the story, add streaks/history, sharpen the news-to-clue mapping.")}
""", "CHAPTER 04 // REFLECTION", "LIMITATIONS & NEXT STEPS", "target", 24, 46))

# ------------------------------------------------------------------ 22c TEAM & ROLES
roles = [
    ("PROJECT LEAD", "Scope, schedule, integration.", "game"),
    ("GAME DEVELOPER", "Pixel game, scenes, mechanics.", "game"),
    ("CRAWLER & DATA", "RSS fetch, clean, label, merge.", "news"),
    ("ML ENGINEER", "Baseline + neural models, eval.", "model"),
    ("FRONTEND / UI", "Editor, HUD, presentation UI.", "gear"),
    ("QA & TESTING", "Pipeline tests, bug hunting.", "target"),
    ("DOCS & PITCH", "Slides, report, live demo.", "book"),
]
accents = ["red", "gold", "navy", "green", "gold", "red", "navy"]
role_html = "".join(
    f'<div class="role-card reveal" style="--i:{i}"><div class="bar {accents[i]}">{t}<img src="assets/icons/{ic}.png" alt=""></div><p>{d}</p></div>'
    for i, (t, d, ic) in enumerate(roles)
)
sections.append(content(f"""
      <div class="role-grid">{role_html}</div>
      <div class="source-line" style="text-align:center; margin-top:22px;">GROUP 2&nbsp;&nbsp;//&nbsp;&nbsp;CHIU WAI YIU · LAI CHUN KUI · LAI WAN YAU SONYA · MAK TSUN WAI MARSIO · WONG CHING WAI · WONG SUI KI · WONG TSZ CHING</div>
      {note("Team slide. Seven members, seven roles. Assign each name to a role before presenting.")}
""", "THE TEAM", "SEVEN ROLES, ONE CASE", "game", 25, 48))

# ------------------------------------------------------------------ 23 CLOSING
sections.append(f"""
<section class="slide title-slide closing" aria-hidden="true">
  <div class="closing-panel">
    <div class="rivet tl"></div><div class="rivet tr"></div>
    <div class="rivet bl"></div><div class="rivet br"></div>
    <div class="case-tag">CASE CLOSED</div>
    <h2 class="closing-title">CASE CLOSED.</h2>
    <p class="closing-sub">Today's news becomes tomorrow's mystery.</p>
    <div class="title-rule"></div>
    <div class="closing-list">
      <div><img src="assets/icons/check.png" alt=""><span>A real news story becomes a playable case.</span></div>
      <div><img src="assets/icons/check.png" alt=""><span>A classical baseline ranks what matters.</span></div>
      <div><img src="assets/icons/check.png" alt=""><span>An honest comparison shows the trade-offs.</span></div>
    </div>
    <div class="closing-bottom">
      <button class="start-btn" data-first>THANK YOU</button>
      <div class="questions">QUESTIONS &gt;&gt;</div>
    </div>
    <div class="closing-end">THE END</div>
    <div class="title-foot">GROUP 2&nbsp;&nbsp;//&nbsp;&nbsp;CHIU WAI YIU · LAI CHUN KUI · LAI WAN YAU SONYA · MAK TSUN WAI MARSIO<br>WONG CHING WAI · WONG SUI KI · WONG TSZ CHING&nbsp;&nbsp;//&nbsp;&nbsp;INT4096 · 2026-27 SEM 1</div>
  </div>
  {note("Close with the three summary lines, then invite questions.")}
</section>""")

# ------------------------------------------------------------------ 24 REFERENCES
ref_left = [
    "Hochreiter, S., &amp; Schmidhuber, J. (1997). Long short-term memory. Neural Computation, 9(8), 1735–1780.",
    "Liu, Y., Ott, M., Goyal, N., Du, J., Joshi, M., Chen, D., Levy, O., Lewis, M., Zettlemoyer, L., &amp; Stoyanov, V. (2019). RoBERTa: A robustly optimized BERT pretraining approach. arXiv:1907.11692.",
    "Media Technology Monitor. (2024). News Alert, 09-05-2024. https://mtm-otm.ca/",
]
ref_right = [
    "Paszke, A., et al. (2019). PyTorch: An imperative style, high-performance deep learning library. Advances in Neural Information Processing Systems, 32.",
    "Pedregosa, F., et al. (2011). Scikit-learn: Machine learning in Python. Journal of Machine Learning Research, 12, 2825–2830.",
    "Sanh, V., Debut, L., Chaumond, J., &amp; Wolf, T. (2019). DistilBERT, a distilled version of BERT: Smaller, faster, cheaper and lighter. arXiv:1910.01108.",
    "Wolf, T., et al. (2020). Transformers: State-of-the-art natural language processing. arXiv:1910.03771.",
]
sections.append(content(f"""
      <div class="prep-cols">
        <div class="prep-col reveal" style="--i:0"><div style="font-size:16px; line-height:1.3; color:var(--ink-soft); padding:16px 4px;">{"<br><br>".join(ref_left)}</div></div>
        <div class="prep-col reveal" style="--i:1"><div style="font-size:16px; line-height:1.3; color:var(--ink-soft); padding:16px 4px;">{"<br><br>".join(ref_right)}</div></div>
      </div>
      {note("References in APA 7 format, citing the statistics source, the models, and the libraries used.")}
""", "REFERENCES", "REFERENCES (APA 7TH)", "book", 27, 44))

HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Pixel Isle — INT4096 Group 2</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E%3Crect width='16' height='16' fill='%23171319'/%3E%3Crect x='3' y='3' width='4' height='4' fill='%23e3a83b'/%3E%3Crect x='9' y='9' width='4' height='4' fill='%239a3434'/%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&family=VT323&display=swap" rel="stylesheet">
<style>
/* ============================================================
   FONTS — local pixel fonts travel with the deck
   ============================================================ */
@font-face {{
  font-family: 'Press Start 2P';
  src: url('assets/fonts/PressStart2P-Regular.ttf') format('truetype');
  font-display: swap;
}}
@font-face {{
  font-family: 'VT323';
  src: url('assets/fonts/VT323-Regular.ttf') format('truetype');
  font-display: swap;
}}

/* ============================================================
   THEME TOKENS — change these to recolour the whole deck
   ============================================================ */
:root {{
  --ink: #171319;
  --ink-soft: #3a2a1e;
  --cream: #f1e4c4;
  --cream-light: #f8eed4;
  --cream-dark: #e3d2ab;
  --gold: #e3a83b;
  --gold-dark: #b97a1e;
  --red: #9a3434;
  --red-dark: #6e2224;
  --green: #7aa549;
  --green-dark: #3f5e2a;
  --navy: #26324f;
  --muted: #6b5a44;
  --display: 'Press Start 2P', monospace;
  --body: 'VT323', monospace;
  --ease: cubic-bezier(0.16, 1, 0.3, 1);
  --stage-bg: #0b0807;
  --slide-bg: #2a1a12;
}}

/* ============================================================
   MANDATORY FIXED-STAGE BASE (from viewport-base.css)
   ============================================================ */
{BASE_CSS}

/* ============================================================
   GLOBAL PIXEL SYSTEM
   ============================================================ */
* {{ box-sizing: border-box; }}
html, body {{ background: var(--stage-bg); }}
body {{ font-family: var(--body); color: var(--ink); -webkit-font-smoothing: none; }}
.deck-viewport {{ background: radial-gradient(circle at 50% 40%, #2a1810 0%, #090604 70%); }}
.deck-stage {{ background: #1a0f0a; }}
.slide::after {{
  content: ""; position: absolute; inset: 0; z-index: 60; pointer-events: none;
  background: repeating-linear-gradient(0deg, rgba(0,0,0,.22) 0 2px, transparent 2px 4px);
  opacity: .32;
}}
.slide {{ image-rendering: pixelated; }}
img {{ image-rendering: pixelated; }}
h1, h2, h3, p, ul, dl, dd, dt {{ margin: 0; }}
button {{ font: inherit; }}

/* backgrounds */
.content-slide {{ background: #2a1a12 url('assets/bg_wood.png') center / cover no-repeat; }}
.section-slide {{ background: #6e2224 url('assets/bg_carpet.png') center / cover no-repeat; }}
.title-slide {{ background: #1a0f0a url('assets/bg_title.png') center / cover no-repeat; }}

/* ============================================================
   PAPER PANEL + HEADER SYSTEM
   ============================================================ */
.panel {{
  position: absolute; left: 60px; top: 49px; width: 1798px; height: 939px;
  background: var(--cream) url('assets/panel_paper.png') center / cover no-repeat;
  border: 6px solid var(--ink);
  box-shadow: 14px 14px 0 rgba(0,0,0,.62);
  overflow: hidden;
}}
.panel::before {{
  content: ""; position: absolute; inset: 0; pointer-events: none;
  background: linear-gradient(90deg, rgba(255,255,255,.06), transparent 28%, transparent 72%, rgba(0,0,0,.04));
}}
.rivet {{ position: absolute; width: 20px; height: 20px; background: var(--gold); border: 2px solid var(--ink); z-index: 3; }}
.rivet.tl {{ left: 1px; top: 1px; }}
.rivet.tr {{ right: 1px; top: 1px; }}
.rivet.bl {{ left: 1px; bottom: 1px; }}
.rivet.br {{ right: 1px; bottom: 1px; }}

.slide-head {{ position: absolute; left: 52px; right: 52px; top: 18px; z-index: 2; }}
.eyebrow {{ font-family: var(--body); font-size: 24px; letter-spacing: 1px; color: var(--muted); }}
.head-row {{ display: flex; align-items: center; justify-content: space-between; gap: 24px; margin-top: 8px; }}
.head-icon {{ width: 72px; height: 72px; flex: 0 0 auto; }}
.slide-title {{
  font-family: var(--display); font-size: 60px; line-height: 1.08; color: var(--ink);
  text-shadow: 3px 3px 0 rgba(227,168,59,.55); max-width: 1590px;
}}
.rule {{ position: relative; height: 4px; background: var(--ink); margin-top: 16px; }}
.rule::before {{ content: ""; position: absolute; left: 0; top: 0; width: 195px; height: 4px; background: var(--red); }}
.slide-body {{ position: absolute; left: 52px; right: 52px; top: 205px; bottom: 40px; z-index: 2; }}
.slide-body.center-body {{ display: flex; flex-direction: column; justify-content: center; }}

/* footer chrome */
.slide-footer, .section-footer {{
  position: absolute; left: 112px; right: 112px; bottom: 16px;
  display: flex; justify-content: space-between; align-items: center;
  font-family: var(--body); font-size: 22px; letter-spacing: 1px; color: var(--gold);
}}
.section-footer {{ color: var(--cream); }}
.page-chip {{
  font-family: var(--display); font-size: 17px; color: var(--gold);
  background: var(--ink); padding: 8px 12px; border: 2px solid var(--ink);
}}

/* ============================================================
   REVEAL + PIXEL MOTION
   ============================================================ */
.reveal {{
  opacity: 0; transform: translateY(28px);
  transition: opacity .55s var(--ease), transform .55s var(--ease);
  transition-delay: calc(var(--i, 0) * 70ms);
}}
.slide.visible .reveal {{ opacity: 1; transform: translateY(0); }}
.spark {{
  position: absolute; width: 12px; height: 12px; background: var(--gold); z-index: 4;
  box-shadow: 0 0 0 4px rgba(227,168,59,.12);
  animation: bob 3.4s ease-in-out infinite;
}}
.spark.s1 {{ left: 120px; bottom: 180px; animation-delay: 0s; }}
.spark.s2 {{ right: 150px; top: 170px; animation-delay: .8s; background: var(--cream); }}
.spark.s3 {{ right: 260px; bottom: 240px; animation-delay: 1.5s; background: var(--red); }}
@keyframes bob {{ 0%,100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-16px); }} }}

/* ============================================================
   TITLE SLIDE
   ============================================================ */
.title-panel {{
  position: absolute; left: 69px; top: 69px; width: 1087px; height: 910px;
  background: var(--cream) url('assets/panel_paper.png') center / cover no-repeat;
  border: 6px solid var(--ink); box-shadow: 14px 14px 0 rgba(0,0,0,.65);
  padding: 52px 56px; overflow: hidden;
}}
.case-tag {{
  display: inline-block; background: var(--red); color: var(--cream);
  font-family: var(--display); font-size: 18px; padding: 12px 20px;
  border: 3px solid var(--ink); box-shadow: 5px 5px 0 var(--ink);
}}
.game-title {{
  margin-top: 52px; font-family: var(--display); font-size: 88px; line-height: 1;
  color: var(--gold); text-shadow: 8px 8px 0 var(--ink); white-space: nowrap;
}}
.type {{
  display: inline-block; overflow: hidden; white-space: nowrap; width: 0;
  border-right: 10px solid var(--gold);
  animation: typing 1.15s steps(10) .35s forwards, blink .8s step-end infinite;
}}
@keyframes typing {{ to {{ width: 10ch; }} }}
@keyframes blink {{ 50% {{ border-color: transparent; }} }}
.tagline {{
  margin-top: 30px; font-family: var(--display); font-size: 26px;
  line-height: 1.5; color: var(--ink);
}}
.title-rule {{ height: 4px; background: var(--ink); margin: 34px 0 22px; }}
.title-desc {{ font-family: var(--body); font-size: 38px; line-height: 1.04; color: var(--ink-soft); }}
.chips {{ display: flex; gap: 20px; margin-top: 28px; }}
.chip {{
  font-family: var(--display); font-size: 15px; padding: 12px 18px;
  background: var(--cream-light); border: 3px solid var(--ink);
}}
.chip.sm {{ font-size: 11px; padding: 8px 10px; }}
.title-bottom {{ display: flex; justify-content: space-between; align-items: flex-end; gap: 24px; margin-top: 38px; }}
.start-btn {{
  font-family: var(--display); font-size: 19px; color: var(--cream);
  background: var(--red); border: 4px solid var(--ink); box-shadow: 8px 8px 0 var(--ink);
  padding: 20px 28px; cursor: pointer; transition: transform .15s var(--ease), box-shadow .15s var(--ease);
}}
.start-btn:hover {{ transform: translate(-2px,-2px); box-shadow: 10px 10px 0 var(--ink); }}
.course {{ font-family: var(--body); font-size: 25px; line-height: 1.05; color: var(--muted); text-align: right; }}
.title-foot {{ position: absolute; left: 56px; bottom: 42px; font-family: var(--body); font-size: 19px; line-height: 1.1; color: var(--muted); }}
.room-tag {{
  position: absolute; right: 64px; bottom: 24px; z-index: 4;
  background: var(--ink); color: var(--gold); font-family: var(--display); font-size: 13px; padding: 10px 16px;
}}

/* ============================================================
   SECTION SLIDES
   ============================================================ */
.section-tag {{
  position: absolute; left: 86px; top: 79px; background: var(--ink); color: var(--gold);
  font-family: var(--display); font-size: 16px; padding: 12px 18px; z-index: 3;
}}
.chapter-label {{ position: absolute; left: 89px; top: 195px; font-family: var(--body); font-size: 30px; color: var(--gold); z-index: 3; }}
.big-number {{
  position: absolute; left: 52px; top: 226px; z-index: 2;
  font-family: var(--display); font-size: 260px; line-height: 1; color: var(--gold);
  text-shadow: 10px 10px 0 var(--ink);
}}
.section-title {{
  position: absolute; left: 640px; top: 300px; z-index: 3;
  font-family: var(--display); font-size: 96px; line-height: 1; color: var(--cream);
  text-shadow: 8px 8px 0 var(--ink);
}}
.section-rule {{ position: absolute; left: 646px; top: 438px; width: 320px; height: 5px; background: var(--gold); z-index: 3; }}
.section-sub {{ position: absolute; left: 644px; top: 482px; z-index: 3; font-family: var(--body); font-size: 52px; line-height: 1.02; color: var(--cream); }}
.chapter-progress {{ position: absolute; left: 62px; bottom: 72px; display: flex; gap: 12px; z-index: 3; }}
.chapter-progress span {{
  width: 70px; height: 44px; display: flex; align-items: center; justify-content: center;
  font-family: var(--display); font-size: 13px; color: var(--cream);
  background: var(--red-dark); border: 2px solid var(--ink);
}}
.chapter-progress span.on {{ background: var(--gold); color: var(--ink); }}
.wasd {{ position: absolute; right: 90px; bottom: 92px; font-family: var(--body); font-size: 26px; color: var(--gold); z-index: 3; }}

/* ============================================================
   AGENDA
   ============================================================ */
.agenda {{ display: flex; flex-direction: column; gap: 18px; }}
.agenda-row {{
  display: flex; height: 148px; background: var(--cream-light);
  border: 4px solid var(--ink); box-shadow: 8px 8px 0 var(--ink);
}}
.agenda-num {{
  width: 140px; display: flex; align-items: center; justify-content: center;
  font-family: var(--display); font-size: 40px; color: var(--cream);
  border-right: 4px solid var(--ink);
}}
.agenda-num.red {{ background: var(--red); }}
.agenda-num.gold {{ background: var(--gold-dark); }}
.agenda-num.navy {{ background: var(--navy); }}
.agenda-num.green {{ background: var(--green-dark); }}
.agenda-copy {{ flex: 1; padding: 18px 28px; }}
.agenda-copy h3 {{ font-family: var(--display); font-size: 22px; }}
.agenda-copy p {{ font-family: var(--body); font-size: 32px; margin-top: 8px; color: var(--ink-soft); }}
.agenda-icon {{ width: 105px; display: flex; align-items: center; justify-content: center; }}
.agenda-icon img {{ width: 64px; height: 64px; }}
.agenda-note {{ margin-top: 26px; text-align: center; font-family: var(--body); font-size: 22px; color: var(--muted); }}

/* ============================================================
   PROBLEM STATS + CARDS
   ============================================================ */
.stats-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 32px; }}
.stat-card {{ position: relative; min-height: 300px; padding: 28px 30px; border: 5px solid var(--ink); box-shadow: 10px 10px 0 rgba(0,0,0,.6); }}
.stat-card.black {{ background: var(--ink); }}
.stat-card.red {{ background: var(--red); }}
.stat-number {{ font-family: var(--display); font-size: 110px; line-height: 1; color: var(--gold); text-shadow: 4px 4px 0 #000; }}
.stat-card.red .stat-number {{ color: var(--cream); text-shadow: 4px 4px 0 var(--red-dark); }}
.stat-label {{ margin-top: 20px; max-width: 640px; font-family: var(--body); font-size: 34px; line-height: 1.02; color: var(--cream); }}
.stat-source {{ position: absolute; left: 30px; bottom: 20px; font-family: var(--display); font-size: 11px; color: var(--cream-dark); }}
.cards-3 {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 28px; margin-top: 32px; }}
.mini-card {{ display: flex; flex-direction: column; min-height: 250px; background: var(--cream-light); border: 4px solid var(--ink); box-shadow: 8px 8px 0 var(--ink); }}
.mini-card .bar, .note-card .bar, .result-card .bar, .role-card .bar {{
  display: flex; align-items: center; justify-content: space-between; gap: 10px;
  padding: 13px 16px; border-bottom: 4px solid var(--ink);
  font-family: var(--display); font-size: 14px; color: var(--cream);
}}
.mini-card .bar img, .note-card .bar img, .result-card .bar img, .role-card .bar img {{ width: 36px; height: 36px; }}
.bar.red {{ background: var(--red); }} .bar.navy {{ background: var(--navy); }}
.bar.gold {{ background: var(--gold-dark); }} .bar.green {{ background: var(--green-dark); }}
.mini-card p {{ flex: 1; display: flex; align-items: center; padding: 20px; font-family: var(--body); font-size: 30px; line-height: 1.02; color: var(--ink-soft); }}
.source-line {{ margin-top: 22px; font-family: var(--body); font-size: 20px; color: var(--muted); }}

/* ============================================================
   ANSWER / TRANSFORMATION
   ============================================================ */
.answer-grid {{ display: grid; grid-template-columns: 1.08fr .92fr; gap: 40px; height: 100%; }}
.goal-list {{ display: flex; flex-direction: column; gap: 20px; }}
.goal {{ display: flex; align-items: stretch; height: 160px; background: var(--cream-light); border: 4px solid var(--ink); box-shadow: 8px 8px 0 var(--ink); }}
.goal-icon {{ width: 120px; display: flex; align-items: center; justify-content: center; border-right: 4px solid var(--ink); }}
.goal-icon.red {{ background: var(--red); }} .goal-icon.gold {{ background: var(--gold-dark); }} .goal-icon.green {{ background: var(--green-dark); }}
.goal-icon img {{ width: 62px; height: 62px; }}
.goal > div:last-child {{ padding: 20px 24px; }}
.goal h3 {{ font-family: var(--display); font-size: 18px; }}
.goal p {{ margin-top: 12px; font-family: var(--body); font-size: 30px; color: var(--ink-soft); }}
.flow-label {{ font-family: var(--display); font-size: 14px; color: var(--muted); margin-bottom: 8px; }}
.flow-card {{ display: flex; align-items: stretch; height: 112px; background: var(--cream-light); border: 4px solid var(--ink); box-shadow: 6px 6px 0 var(--ink); }}
.flow-icon {{ width: 92px; display: flex; align-items: center; justify-content: center; border-right: 4px solid var(--ink); }}
.flow-icon.navy {{ background: var(--navy); }} .flow-icon.gold {{ background: var(--gold-dark); }}
.flow-icon.red {{ background: var(--red); }} .flow-icon.green {{ background: var(--green-dark); }}
.flow-icon img {{ width: 54px; height: 54px; }}
.flow-card > div:last-child {{ padding: 14px 18px; }}
.flow-card h3 {{ font-family: var(--display); font-size: 14px; }}
.flow-card p {{ margin-top: 8px; font-family: var(--body); font-size: 26px; color: var(--ink-soft); }}
.flow-arrow {{ height: 22px; display: flex; align-items: center; justify-content: center; font-family: var(--body); font-size: 26px; color: var(--red); }}

/* ============================================================
   GAME DEMO
   ============================================================ */
.game-layout {{ display: grid; grid-template-columns: 1238px 1fr; gap: 42px; height: 100%; }}
.game-frame {{ height: 660px; border: 6px solid var(--ink); box-shadow: 12px 12px 0 var(--ink); background: #000; overflow: hidden; }}
.game-frame img {{ display: block; width: 100%; height: 100%; object-fit: cover; object-position: center; }}
.game-caption {{ margin-top: 12px; font-family: var(--body); font-size: 22px; color: var(--muted); }}
.game-side {{ display: flex; flex-direction: column; }}
.control {{ display: flex; height: 78px; margin-bottom: 16px; background: var(--cream-light); border: 4px solid var(--ink); box-shadow: 6px 6px 0 var(--ink); }}
.control .key {{ width: 100px; display: flex; align-items: center; justify-content: center; background: var(--ink); color: var(--gold); font-family: var(--display); font-size: 15px; border-right: 4px solid var(--ink); }}
.control .action {{ display: flex; align-items: center; padding-left: 20px; font-family: var(--display); font-size: 16px; }}
.note-card {{ background: var(--cream-light); border: 4px solid var(--ink); box-shadow: 8px 8px 0 var(--ink); display: flex; flex-direction: column; }}
.case-note {{ margin-top: 4px; flex: 0 0 340px; }}
.note-card .body {{ flex: 1; display: flex; align-items: center; padding: 22px 20px; font-family: var(--body); font-size: 28px; line-height: 1.05; color: var(--ink-soft); }}
.live-demo {{ margin-top: 12px; text-align: right; font-family: var(--display); font-size: 13px; color: var(--red); }}

/* ============================================================
   PIPELINE
   ============================================================ */
.pipe-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 34px 40px; }}
.pipe-box {{ position: relative; min-height: 232px; padding: 20px; background: var(--cream-light); border: 4px solid var(--ink); box-shadow: 8px 8px 0 var(--ink); }}
.pipe-box .num {{ position: absolute; left: 0; top: 0; padding: 10px 13px; border-right: 4px solid var(--ink); border-bottom: 4px solid var(--ink); font-family: var(--display); font-size: 13px; color: var(--cream); }}
.pipe-box .num.red {{ background: var(--red); }} .pipe-box .num.gold {{ background: var(--gold-dark); }}
.pipe-box .num.navy {{ background: var(--navy); }} .pipe-box .num.green {{ background: var(--green-dark); }}
.pipe-box img {{ position: absolute; right: 18px; top: 16px; width: 48px; height: 48px; }}
.pipe-box h3 {{ margin-top: 44px; font-family: var(--display); font-size: 16px; }}
.pipe-box p {{ margin-top: 12px; font-family: var(--body); font-size: 26px; line-height: 1.02; color: var(--ink-soft); }}
.pipe-box:not(:nth-child(4n))::after {{
  content: ""; position: absolute; right: -33px; top: 100px; z-index: 2;
  border-left: 18px solid var(--red); border-top: 12px solid transparent; border-bottom: 12px solid transparent;
}}
.banner {{ margin-top: 32px; padding: 20px 28px; text-align: center; background: var(--ink); border: 4px solid var(--gold); font-family: var(--display); font-size: 17px; line-height: 1.5; color: var(--gold); }}

/* ============================================================
   DATASET + CHARTS
   ============================================================ */
.dataset-grid {{ display: grid; grid-template-columns: .88fr 1.12fr; gap: 40px; height: 100%; }}
.dataset-left {{ display: flex; flex-direction: column; }}
.dataset-stats {{ display: grid; grid-template-columns: 1fr 1fr; gap: 22px; }}
.dataset-stat {{ min-height: 190px; padding: 22px; background: var(--cream-light); border: 4px solid var(--ink); box-shadow: 6px 6px 0 var(--ink); }}
.dataset-stat .n {{ font-family: var(--display); font-size: 42px; color: var(--red); }}
.dataset-stat .l {{ margin-top: 20px; font-family: var(--body); font-size: 28px; color: var(--ink-soft); }}
.dataset-note {{ margin-top: auto; padding-top: 22px; font-family: var(--body); font-size: 17px; color: var(--ink-soft); }}
.dataset-note p {{ margin-bottom: 8px; }}
.dataset-note .muted {{ color: var(--muted); }}
.chart-ph {{ position: relative; height: 420px; background-color: var(--cream-dark); background-size: cover; background-position: center; border: 5px dashed var(--red); box-shadow: 8px 8px 0 var(--ink); overflow: hidden; }}
.chart-ph .fig {{ position: absolute; left: 24px; top: 22px; padding: 8px 14px; background: var(--ink); color: var(--gold); font-family: var(--display); font-size: 12px; }}
.chart-plate {{ position: absolute; left: 24px; top: 74px; max-width: calc(100% - 48px); padding: 18px 22px; background: var(--cream-light); border: 4px solid var(--ink); }}
.chart-plate h3 {{ font-family: var(--display); font-size: 15px; line-height: 1.4; color: var(--red); text-align: center; }}
.chart-plate p {{ margin-top: 8px; font-family: var(--body); font-size: 25px; line-height: 1.02; color: var(--ink-soft); text-align: center; }}
.chart-ph .drop {{ position: absolute; right: 18px; bottom: 12px; font-family: var(--body); font-size: 19px; color: var(--muted); }}
.chart-ph.solid {{ border: 5px solid var(--ink); background: var(--cream-light); }}
.chart-pic {{ position: absolute; left: 24px; top: 60px; right: 24px; bottom: 18px; max-width: calc(100% - 48px); max-height: calc(100% - 78px); object-fit: contain; image-rendering: pixelated; }}
.chart-caption {{ margin-top: 10px; font-family: var(--body); font-size: 18px; color: var(--muted); }}

/* ============================================================
   PREPROCESSING
   ============================================================ */
.prep-wrap {{ display: flex; flex-direction: column; height: 100%; gap: 24px; }}
.prep-cols {{ display: grid; grid-template-columns: 1fr 1fr; gap: 36px; }}
.prep-bar {{ padding: 14px 18px; border: 4px solid var(--ink); font-family: var(--display); font-size: 15px; color: var(--cream); }}
.prep-bar.red {{ background: var(--red); }} .prep-bar.green {{ background: var(--green-dark); }}
.prep-col ul {{ list-style: none; padding: 22px 6px 0 6px; font-family: var(--body); font-size: 32px; line-height: 1.08; color: var(--ink-soft); }}
.prep-col li {{ position: relative; padding-left: 30px; margin-bottom: 12px; }}
.prep-col li::before {{ content: ">"; position: absolute; left: 0; color: var(--red); font-weight: bold; }}
.why {{ padding: 16px 20px; border: 4px dashed var(--red); background: var(--cream-light); font-family: var(--body); font-size: 28px; color: var(--red); }}
.terminal {{ margin-top: auto; padding: 18px 24px; background: var(--ink); border: 3px solid #000; font-family: var(--body); font-size: 28px; line-height: 1.2; color: var(--green); }}
.terminal .ok {{ margin-top: 6px; font-size: 20px; color: var(--cream-dark); }}
.example {{ padding: 16px 22px; background: var(--ink); border: 3px solid #000; color: var(--cream); font-family: var(--body); font-size: 24px; }}
.example-label {{ margin-bottom: 8px; font-family: var(--display); font-size: 9px; color: var(--gold); }}
.example-row {{ display: flex; gap: 14px; align-items: baseline; margin-top: 4px; }}
.example-row code {{ font-family: var(--body); font-size: 24px; color: var(--cream); }}
.example-row .raw {{ font-family: var(--display); font-size: 9px; color: var(--red); }}
.example-row .clean {{ font-family: var(--display); font-size: 9px; color: var(--green); }}

/* ============================================================
   METHOD
   ============================================================ */
.method-wrap {{ display: flex; flex-direction: column; height: 100%; gap: 24px; }}
.method-q {{ font-family: var(--display); font-size: 20px; color: var(--red); }}
.class-grid {{ flex: 1; display: grid; grid-template-columns: repeat(3, 1fr); gap: 28px; }}
.class-card {{ display: flex; min-height: 320px; background: var(--cream-light); border: 4px solid var(--ink); box-shadow: 8px 8px 0 var(--ink); }}
.class-num {{ width: 150px; display: flex; align-items: center; justify-content: center; border-right: 4px solid var(--ink); font-family: var(--display); font-size: 64px; color: var(--cream); }}
.class-num.muted {{ background: #8d7a5a; }} .class-num.gold {{ background: var(--gold-dark); }} .class-num.red {{ background: var(--red); }}
.class-copy {{ padding: 24px; }}
.class-copy h3 {{ font-family: var(--display); font-size: 18px; }}
.class-copy p {{ margin-top: 18px; font-family: var(--body); font-size: 30px; line-height: 1.03; color: var(--ink-soft); }}
.model-banner {{ padding: 24px 28px; background: var(--ink); border: 4px solid var(--gold); box-shadow: 8px 8px 0 var(--ink); }}
.model-title {{ font-family: var(--display); font-size: 18px; color: var(--gold); }}
.model-specs {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 26px; margin-top: 20px; }}
.model-specs span {{ font-family: var(--display); font-size: 11px; color: var(--green); }}
.model-specs p {{ margin-top: 8px; font-family: var(--body); font-size: 27px; line-height: 1.04; color: var(--cream); }}

/* ============================================================
   WHY / MODEL CARD
   ============================================================ */
.why-grid {{ display: grid; grid-template-columns: 1.3fr .7fr; gap: 38px; height: 100%; }}
.why-left {{ display: flex; flex-direction: column; }}
.reason {{ display: flex; align-items: center; gap: 18px; min-height: 96px; margin-bottom: 12px; padding: 14px 20px; background: var(--cream-light); border: 4px solid var(--ink); box-shadow: 6px 6px 0 var(--ink); font-family: var(--body); font-size: 29px; line-height: 1.02; color: var(--ink-soft); }}
.reason img {{ width: 42px; height: 42px; flex: 0 0 auto; }}
.also {{ display: flex; align-items: center; gap: 10px; margin-top: 4px; flex-wrap: wrap; }}
.also > span:first-child {{ font-family: var(--display); font-size: 11px; color: var(--muted); margin-right: 4px; }}
.model-card {{ display: flex; flex-direction: column; padding: 26px 28px; background: var(--ink); border: 4px solid var(--ink); box-shadow: 8px 8px 0 var(--ink); }}
.model-card h3 {{ font-family: var(--display); font-size: 17px; color: var(--gold); }}
.model-card-rule {{ height: 3px; background: var(--gold); margin: 16px 0 18px; }}
.model-card dl {{ display: grid; grid-template-columns: 1fr 1.2fr; gap: 18px 12px; }}
.model-card dt {{ font-family: var(--display); font-size: 10px; color: var(--green); }}
.model-card dd {{ font-family: var(--body); font-size: 24px; color: var(--cream); }}
.model-foot {{ margin-top: auto; padding-top: 16px; border-top: 3px solid var(--gold); font-family: var(--display); font-size: 10px; line-height: 1.6; color: var(--green); }}

/* ============================================================
   SPLIT
   ============================================================ */
.split-wrap {{ display: flex; flex-direction: column; height: 100%; gap: 22px; }}
.split-bar {{ display: flex; height: 86px; border: 4px solid var(--ink); box-shadow: 6px 6px 0 var(--ink); }}
.split-bar .seg {{ display: flex; align-items: center; justify-content: center; font-family: var(--display); font-size: 14px; }}
.split-bar .train {{ flex: 8; background: var(--gold); color: var(--ink); }}
.split-bar .val {{ flex: 1; background: var(--green); color: var(--cream); border-left: 4px solid var(--ink); }}
.split-bar .test {{ flex: 1; background: var(--red); color: var(--cream); border-left: 4px solid var(--ink); }}
.split-note {{ text-align: center; font-family: var(--body); font-size: 25px; color: var(--muted); }}
.role-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 28px; }}
.role-card {{ background: var(--cream-light); border: 4px solid var(--ink); box-shadow: 7px 7px 0 var(--ink); }}
.role-card p {{ padding: 22px 20px; font-family: var(--body); font-size: 30px; line-height: 1.02; color: var(--ink-soft); }}
.metric-row {{ display: flex; flex-wrap: wrap; align-items: center; gap: 14px; }}
.metric-label {{ flex: 0 0 100%; width: auto; margin-bottom: 2px; font-family: var(--display); font-size: 11px; color: var(--muted); }}
.metric {{ padding: 14px 18px; background: var(--ink); color: var(--gold); font-family: var(--display); font-size: 12px; }}
.seed {{ margin-left: auto; padding: 16px 28px; border: 4px dashed var(--red); font-family: var(--body); font-size: 25px; line-height: 1.05; color: var(--red); text-align: center; }}
.split-foot {{ margin-top: auto; font-family: var(--body); font-size: 22px; color: var(--ink-soft); }}

/* ============================================================
   RESULTS TABLE
   ============================================================ */
.pixel-table {{ width: 100%; border-collapse: collapse; background: var(--cream-light); border: 4px solid var(--ink); box-shadow: 8px 8px 0 var(--ink); font-family: var(--body); font-size: 27px; }}
.pixel-table th {{ padding: 14px; background: var(--ink); color: var(--gold); font-family: var(--display); font-size: 12px; text-align: left; border: 3px solid var(--ink); }}
.pixel-table td {{ padding: 12px 14px; border: 3px solid var(--ink); }}
.pixel-table td.center {{ text-align: center; }}
.pixel-table td.tbd {{ text-align: center; color: var(--red); }}
.pixel-table tr.best td {{ background: var(--cream-dark); font-weight: bold; }}
.results-chart {{ margin-top: 24px; }}
.results-chart .chart-ph {{ height: 330px; }}

/* ============================================================
   DOUBLE-COLUMN RESULT SLIDES
   ============================================================ */
.double-grid {{ display: grid; grid-template-columns: 1.25fr .75fr; gap: 36px; height: 100%; }}
.double-grid.wide-left {{ grid-template-columns: 1.05fr .95fr; }}
.double-grid .chart-ph {{ height: 620px; }}
.side-card {{ display: flex; flex-direction: column; background: var(--cream-light); border: 4px solid var(--ink); box-shadow: 8px 8px 0 var(--ink); }}
.side-card .bar {{ display: flex; align-items: center; padding: 14px 18px; border-bottom: 4px solid var(--ink); font-family: var(--display); font-size: 14px; color: var(--cream); }}
.side-card ul {{ list-style: none; padding: 22px 22px 12px; font-family: var(--body); font-size: 27px; line-height: 1.07; color: var(--ink-soft); }}
.side-card li {{ position: relative; padding-left: 26px; margin-bottom: 14px; }}
.side-card li::before {{ content: ">"; position: absolute; left: 0; color: var(--red); font-weight: bold; }}
.side-card b {{ color: var(--ink); }}
.side-note {{ margin: auto 22px 16px; padding: 14px 16px; border: 3px dashed var(--gold-dark); background: var(--cream); font-family: var(--display); font-size: 10px; line-height: 1.7; color: var(--ink-soft); text-align: center; }}
.side-strip {{ margin: 0 20px 20px; padding: 16px 12px; background: var(--ink); color: var(--gold); font-family: var(--display); font-size: 13px; line-height: 1.6; text-align: center; }}

/* ============================================================
   RESULTS SHOW
   ============================================================ */
.results-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 26px; }}
.result-card {{ display: flex; flex-direction: column; min-height: 238px; background: var(--cream-light); border: 4px solid var(--ink); box-shadow: 8px 8px 0 var(--ink); }}
.result-card p {{ flex: 1; display: flex; align-items: center; padding: 24px 22px; font-family: var(--body); font-size: 32px; line-height: 1.02; color: var(--ink-soft); }}

/* ============================================================
   IMPLICATIONS
   ============================================================ */
.impact-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 30px; }}
.impact-card {{ position: relative; min-height: 316px; padding: 22px; background: var(--cream-light); border: 4px solid var(--ink); box-shadow: 8px 8px 0 var(--ink); }}
.impact-num {{ font-family: var(--display); font-size: 24px; color: var(--red); }}
.impact-card img {{ position: absolute; right: 18px; top: 18px; width: 44px; height: 44px; }}
.impact-card h3 {{ margin-top: 46px; font-family: var(--display); font-size: 14px; }}
.impact-card p {{ margin-top: 16px; font-family: var(--body); font-size: 28px; line-height: 1.02; color: var(--ink-soft); }}
.impact-card:not(:nth-child(4n))::after {{ content: ""; position: absolute; right: -27px; top: 140px; border-left: 18px solid var(--red); border-top: 12px solid transparent; border-bottom: 12px solid transparent; }}
.impact-bottom {{ display: grid; grid-template-columns: 1fr 1fr; gap: 32px; margin-top: 32px; }}
.impact-big {{ padding: 22px 26px; min-height: 154px; border: 4px solid var(--ink); box-shadow: 8px 8px 0 var(--ink); }}
.impact-big.red {{ background: var(--red); }} .impact-big.green {{ background: var(--green-dark); }}
.impact-big span {{ font-family: var(--display); font-size: 11px; color: var(--cream); }}
.impact-big p {{ margin-top: 24px; font-family: var(--body); font-size: 38px; color: var(--cream); }}
.impact-line {{ margin-top: 22px; text-align: center; font-family: var(--display); font-size: 14px; color: var(--ink); }}

/* ============================================================
   CHALLENGES / LEARNINGS
   ============================================================ */
.challenge-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 26px; }}
.challenge {{ display: flex; min-height: 300px; background: var(--cream-light); border: 4px solid var(--ink); box-shadow: 8px 8px 0 var(--ink); }}
.challenge-num {{ width: 95px; display: flex; align-items: center; justify-content: center; border-right: 4px solid var(--ink); font-family: var(--display); font-size: 34px; color: var(--cream); }}
.challenge-num.red {{ background: var(--red); }} .challenge-num.gold {{ background: var(--gold-dark); }}
.challenge-num.navy {{ background: var(--navy); }} .challenge-num.green {{ background: var(--green-dark); }}
.challenge > div:last-child {{ padding: 24px 26px; }}
.challenge h3 {{ font-family: var(--display); font-size: 15px; }}
.challenge p {{ margin-top: 18px; font-family: var(--body); font-size: 29px; line-height: 1.03; color: var(--ink-soft); }}
.challenge-line {{ margin-top: 26px; text-align: center; font-family: var(--display); font-size: 14px; color: var(--red); }}
.learn-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px 28px; }}
.learn {{ display: flex; align-items: stretch; min-height: 132px; background: var(--cream-light); border: 4px solid var(--ink); box-shadow: 6px 6px 0 var(--ink); }}
.learn-num {{ width: 90px; display: flex; align-items: center; justify-content: center; background: var(--ink); color: var(--gold); font-family: var(--display); font-size: 22px; }}
.learn p {{ flex: 1; display: flex; align-items: center; padding: 16px 22px; font-family: var(--body); font-size: 30px; line-height: 1.02; color: var(--ink-soft); }}

/* ============================================================
   CLOSING
   ============================================================ */
.closing-panel {{
  position: absolute; left: 92px; top: 95px; width: 1230px; height: 857px;
  background: var(--cream) url('assets/panel_paper.png') center / cover no-repeat;
  border: 6px solid var(--ink); box-shadow: 14px 14px 0 rgba(0,0,0,.65);
  padding: 54px 58px; overflow: hidden;
}}
.closing-title {{ margin-top: 52px; font-family: var(--display); font-size: 72px; line-height: 1; color: var(--ink); text-shadow: 5px 5px 0 var(--gold); }}
.closing-sub {{ margin-top: 26px; font-family: var(--body); font-size: 40px; color: var(--red); }}
.closing-list {{ margin-top: 22px; }}
.closing-list div {{ display: flex; align-items: center; gap: 16px; margin-bottom: 16px; font-family: var(--body); font-size: 32px; color: var(--ink-soft); }}
.closing-list img {{ width: 36px; height: 36px; }}
.closing-bottom {{ display: flex; align-items: center; gap: 30px; margin-top: 34px; }}
.questions {{ font-family: var(--display); font-size: 24px; color: var(--ink); }}
.qr-zone {{ position: absolute; right: 88px; top: 240px; width: 410px; text-align: center; z-index: 3; }}
.qr-box {{ width: 410px; height: 410px; display: flex; align-items: center; justify-content: center; background: var(--cream-light); border: 5px dashed var(--ink); font-family: var(--display); font-size: 16px; line-height: 1.8; color: var(--muted); }}
.qr-repo {{ display: inline-block; margin-top: 24px; padding: 8px 10px; background: rgba(10,7,5,.78); font-family: var(--body); font-size: 20px; color: var(--cream); }}
.qr-scan {{ display: inline-block; margin-top: 18px; padding: 8px 10px; background: rgba(10,7,5,.78); font-family: var(--display); font-size: 12px; color: var(--gold); }}
.closing-end {{ position: absolute; left: 58px; bottom: 112px; font-family: var(--display); font-size: 24px; letter-spacing: 4px; color: var(--gold); opacity: .78; }}

/* ============================================================
   DECK CONTROLS + NOTES + EDIT
   ============================================================ */
.deck-controls {{
  display: flex; align-items: center; gap: 12px; padding: 8px 12px;
  background: rgba(10,7,5,.72); border: 2px solid rgba(227,168,59,.35);
  backdrop-filter: blur(4px); z-index: 2000;
}}
.deck-controls button {{
  width: 42px; height: 36px; background: var(--ink); color: var(--gold);
  border: 2px solid var(--gold-dark); cursor: pointer; font-family: var(--display); font-size: 12px;
}}
.deck-controls button:hover {{ background: var(--red-dark); }}
.progress {{ width: 160px; height: 10px; background: #2a1a12; border: 2px solid var(--gold-dark); }}
#progressFill {{ width: 4%; height: 100%; background: var(--gold); transition: width .35s var(--ease); }}
.counter {{ min-width: 74px; text-align: center; font-family: var(--display); font-size: 10px; color: var(--gold); }}
.notes-panel {{
  position: fixed; left: 50%; bottom: 84px; transform: translateX(-50%);
  width: min(1100px, 84vw); max-height: 24vh; overflow: auto; display: none;
  background: rgba(10,7,5,.94); border: 3px solid var(--gold-dark);
  color: var(--cream); padding: 16px 20px; z-index: 2100;
  font-family: var(--body); font-size: 20px; line-height: 1.2;
}}
.notes-panel.show {{ display: block; }}
.notes-title {{ font-family: var(--display); font-size: 10px; color: var(--gold); margin-bottom: 8px; }}
.notes {{ display: none; }}

.edit-hotzone {{ position: fixed; top: 0; left: 0; width: 80px; height: 80px; z-index: 10000; cursor: pointer; }}
.edit-toggle, .edit-save {{
  position: fixed; left: 16px; z-index: 10001; opacity: 0; pointer-events: none;
  transition: opacity .3s ease; background: var(--ink); color: var(--gold);
  border: 2px solid var(--gold-dark); font-family: var(--display); font-size: 11px;
  padding: 12px 14px; cursor: pointer;
}}
.edit-toggle {{ top: 16px; }}
.edit-save {{ top: 64px; }}
.edit-toggle.show, .edit-toggle.active, .edit-save.show, .edit-save.active {{ opacity: 1; pointer-events: auto; }}
body.editing .slide.active {{ outline: 6px dashed var(--gold); outline-offset: -12px; }}
body.editing .slide.active * {{ cursor: text; }}
.edit-hint {{
  position: fixed; top: 16px; right: 16px; z-index: 10001; display: none;
  padding: 10px 14px; background: var(--ink); border: 2px solid var(--gold-dark);
  color: var(--gold); font-family: var(--body); font-size: 18px;
}}
body.editing .edit-hint {{ display: block; }}

/* print colours */
@media print {{
  * {{ -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }}
}}
</style>
</head>
<body>
<div class="edit-hotzone" id="editHotzone"></div>
<button class="edit-toggle" id="editToggle" title="Edit mode (E)">E EDIT</button>
<button class="edit-save" id="editSave" title="Save HTML (Ctrl+S)">SAVE</button>
<div class="edit-hint">EDIT MODE // E to exit // Ctrl+S to save</div>

<div class="deck-viewport">
  <main class="deck-stage" id="deckStage">
    {''.join(sections)}
  </main>
</div>

<div class="deck-controls">
  <button id="prevBtn" aria-label="Previous slide">&lt;</button>
  <div class="progress"><div id="progressFill"></div></div>
  <div class="counter" id="counter">01 / {TOTAL}</div>
  <button id="nextBtn" aria-label="Next slide">&gt;</button>
  <button id="notesBtn" aria-label="Toggle speaker notes">N</button>
</div>

<div class="notes-panel" id="notesPanel">
  <div class="notes-title">SPEAKER NOTES</div>
  <div id="notesText"></div>
</div>

<script>
/* ============================================================
   SLIDE PRESENTATION CONTROLLER
   Fixed 1920×1080 stage scaled as one unit. Arrow keys, space,
   wheel, swipe, notes, edit mode, local save, and HTML download.
   ============================================================ */
class PixelDeck {{
  constructor() {{
    this.stage = document.getElementById('deckStage');
    this.slides = [...this.stage.querySelectorAll('.slide')];
    this.current = 0;
    this.scale();
    window.addEventListener('resize', () => this.scale());
    this.bind();
    this.show(0);
  }}

  scale() {{
    const f = Math.min(window.innerWidth / 1920, window.innerHeight / 1080);
    const x = (window.innerWidth - 1920 * f) / 2;
    const y = (window.innerHeight - 1080 * f) / 2;
    this.stage.style.transform = `translate(${{x}}px, ${{y}}px) scale(${{f}})`;
  }}

  bind() {{
    document.getElementById('prevBtn').addEventListener('click', () => this.prev());
    document.getElementById('nextBtn').addEventListener('click', () => this.next());
    document.getElementById('notesBtn').addEventListener('click', () => this.toggleNotes());
    this.stage.addEventListener('click', (e) => {{
      if (e.target.closest('[data-next]')) this.next();
      if (e.target.closest('[data-first]')) this.show(0);
    }});
    document.addEventListener('keydown', (e) => {{
      if (e.target.isContentEditable) {{
        if (e.key === 'Escape') this.toggleEdit();
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') this.saveHTML();
        return;
      }}
      if (['ArrowRight', 'ArrowDown', ' ', 'PageDown'].includes(e.key)) {{ e.preventDefault(); this.next(); }}
      if (['ArrowLeft', 'ArrowUp', 'PageUp'].includes(e.key)) {{ e.preventDefault(); this.prev(); }}
      if (e.key === 'Home') {{ e.preventDefault(); this.show(0); }}
      if (e.key === 'End') {{ e.preventDefault(); this.show(this.slides.length - 1); }}
      if (e.key.toLowerCase() === 'n') this.toggleNotes();
      if (e.key.toLowerCase() === 'e') this.toggleEdit();
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {{ e.preventDefault(); this.saveHTML(); }}
    }});
    let wheelLock = false;
    window.addEventListener('wheel', (e) => {{
      if (wheelLock) return;
      wheelLock = true;
      setTimeout(() => wheelLock = false, 650);
      if (e.deltaY > 18) this.next();
      if (e.deltaY < -18) this.prev();
    }}, {{ passive: true }});
    let sx = 0, sy = 0;
    window.addEventListener('touchstart', (e) => {{
      sx = e.touches[0].clientX; sy = e.touches[0].clientY;
    }}, {{ passive: true }});
    window.addEventListener('touchend', (e) => {{
      const dx = e.changedTouches[0].clientX - sx;
      const dy = e.changedTouches[0].clientY - sy;
      if (Math.abs(dx) > 50 || Math.abs(dy) > 50) {{
        if (Math.abs(dx) > Math.abs(dy)) {{ dx < 0 ? this.next() : this.prev(); }}
        else {{ dy < 0 ? this.next() : this.prev(); }}
      }}
    }}, {{ passive: true }});
  }}

  show(i) {{
    this.current = Math.max(0, Math.min(i, this.slides.length - 1));
    this.slides.forEach((s, idx) => {{
      s.classList.toggle('active', idx === this.current);
      s.classList.toggle('visible', idx === this.current);
      s.setAttribute('aria-hidden', idx === this.current ? 'false' : 'true');
    }});
    document.getElementById('counter').textContent = String(this.current + 1).padStart(2, '0') + ' / {TOTAL}';
    document.getElementById('progressFill').style.width = ((this.current + 1) / this.slides.length * 100) + '%';
    this.updateNotes();
    if (document.body.classList.contains('editing')) this.applyEditing();
  }}

  next() {{ this.show(this.current + 1); }}
  prev() {{ this.show(this.current - 1); }}

  updateNotes() {{
    const n = this.slides[this.current].querySelector('.notes');
    document.getElementById('notesText').textContent = n ? n.textContent.trim() : 'No notes for this slide.';
  }}

  toggleNotes() {{
    document.getElementById('notesPanel').classList.toggle('show');
  }}

  toggleEdit() {{
    const on = document.body.classList.toggle('editing');
    document.getElementById('editToggle').classList.toggle('active', on);
    document.getElementById('editSave').classList.toggle('active', on);
    document.getElementById('editToggle').classList.toggle('show', on);
    document.getElementById('editSave').classList.toggle('show', on);
    this.applyEditing();
  }}

  applyEditing() {{
    const on = document.body.classList.contains('editing');
    this.slides.forEach(s => s.removeAttribute('contenteditable'));
    if (on) {{
      const active = this.slides[this.current];
      active.setAttribute('contenteditable', 'true');
      active.focus();
    }}
  }}

  saveHTML() {{
    const html = '<!DOCTYPE html>\\n' + document.documentElement.outerHTML;
    const blob = new Blob([html], {{ type: 'text/html' }});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'Pixel_Isle_INT4096_edited.html';
    a.click();
    URL.revokeObjectURL(a.href);
  }}
}}

/* Restore locally edited copy, if any, before starting the deck. */
const saved = localStorage.getItem('pixel-isle-deck-v1');
const stage = document.getElementById('deckStage');
if (saved) {{
  stage.innerHTML = saved;
  stage.querySelectorAll('[contenteditable]').forEach(el => el.removeAttribute('contenteditable'));
}}

const deck = new PixelDeck();
window.deck = deck;

/* Auto-save edits after typing stops. */
let saveTimer = null;
stage.addEventListener('input', () => {{
  if (!document.body.classList.contains('editing')) return;
  clearTimeout(saveTimer);
  saveTimer = setTimeout(() => {{
    localStorage.setItem('pixel-isle-deck-v1', stage.innerHTML);
  }}, 700);
}});

/* Edit toggle visibility: required hover grace-period pattern. */
const hotzone = document.getElementById('editHotzone');
const editToggle = document.getElementById('editToggle');
const editSave = document.getElementById('editSave');
let hideTimer = null;
function showEditButtons() {{
  clearTimeout(hideTimer);
  editToggle.classList.add('show');
  editSave.classList.add('show');
}}
function hideEditButtons() {{
  hideTimer = setTimeout(() => {{
    if (!document.body.classList.contains('editing')) {{
      editToggle.classList.remove('show');
      editSave.classList.remove('show');
    }}
  }}, 400);
}}
hotzone.addEventListener('mouseenter', showEditButtons);
hotzone.addEventListener('mouseleave', hideEditButtons);
hotzone.addEventListener('click', () => deck.toggleEdit());
editToggle.addEventListener('mouseenter', showEditButtons);
editSave.addEventListener('mouseenter', showEditButtons);
editToggle.addEventListener('mouseleave', hideEditButtons);
editSave.addEventListener('mouseleave', hideEditButtons);
editToggle.addEventListener('click', () => deck.toggleEdit());
editSave.addEventListener('click', () => deck.saveHTML());

/* Reset saved edits: Shift+R */
document.addEventListener('keydown', (e) => {{
  if (e.shiftKey && e.key.toLowerCase() === 'r' && !e.target.isContentEditable) {{
    localStorage.removeItem('pixel-isle-deck-v1');
    location.reload();
  }}
}});
</script>
</body>
</html>
"""

with open(OUT, "w", encoding="utf-8") as f:
    f.write(HTML)
print("wrote", OUT, "slides:", len(sections), "bytes:", len(HTML.encode("utf-8")))




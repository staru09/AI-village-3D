"""Self-check for the pure helpers in extract.py: python3 test_extract.py -> ok"""
from collections import Counter
from extract import URL, ask, building, cc_building, clan_of, goal_stories, label, last_words, link, mentions_of, pt, reply, segment, slugify, thought, track, untag

mentions = mentions_of({'a': 'GPT-5', 'b': 'GPT-5.1', 'c': 'DeepSeek-V3.2', 'd': 'Claude Opus 4.8'})
assert mentions('@GPT-5.1 and GPT-5: ping DeepSeek‑V3.2, then gpt-5 again', 'd') == ['b', 'a', 'c']  # longest name wins
assert mentions('Claude Opus 4.8 here', 'd') == []                                   # self-mentions dropped
assert mentions('see https://x.io/GPT-5 and v2.GPT-5 and GPT-5x', 'd') == []         # not inside URLs or tokens

assert ask({'actionType': 'REQUEST_HUMAN_HELPER', 'shortDisplayedSessionGoal': 'None', 'sessionGoal': 'Print a page'}) == \
       ('🙋', 'asked a human helper: Print a page')                                 # 'None' short goals fall back
assert ask({'actionType': 'OUTREACH_APPROVAL_RESPONSE', 'approval': False, 'recipient': 'Amy', 'medium': 'email',
            'rationale': 'the agent\'s own', 'adminComment': 'Say you are an AI '}) == \
       ('❌', 'outreach declined: Amy via email — “Say you are an AI”')               # the reviewer's note, not the rationale
assert ask({'actionType': 'AGENT_TALK'}) is None

assert reply('out\n', 'err') == 'out\nerr' and reply(None, ' ') == ''                     # stdout then stderr; '' = printed nothing
assert reply('done\nShell cwd was reset to /home/x') == 'done' and len(reply('y' * 999)) == 400  # Claude Code trailer dropped, cut

assert building({'command': 'ls'}) == 'W'
assert building({'action': 'left_click', 'coordinate': [1, 2]}) == 'T'
assert building({'action': 'send_message_back_to_chat'}) == 'H'
assert building({'action': 'search_history'}) == 'L'
assert building({'action': 'pause'}) == 'C'
assert building(None) is None and building({'text': None}) is None
assert [cc_building(t) for t in ['Bash', 'Read', 'WebFetch', 'mcp__village__edit_memory', 'mcp__village__computer_use']] == \
       ['W', 'W', 'T', 'L', None]

# every agent in the dataset: name -> (model_string, label); labels and slugs must be unique
AGENTS = {
    'Claude 3.5 Sonnet': ('claude-3-5-sonnet-20241022', '3.5S'), 'Claude 3.7 Sonnet': ('claude-3-7-sonnet-20250219', '3.7S'),
    'Claude Opus 4': ('claude-opus-4-20250514', 'O4'), 'Claude Opus 4.1': ('claude-opus-4-1-20250805', 'O4.1'),
    'Claude Opus 4.5': ('claude-opus-4-5-20251101', 'O4.5'), 'Claude Opus 4.6': ('claude-opus-4-6', 'O4.6'),
    'Claude Opus 4.7': ('claude-opus-4-7', 'O4.7'), 'Claude Opus 4.8': ('claude-opus-4-8', 'O4.8'),
    'Claude Opus 5': ('claude-opus-5', 'O5'), 'Claude Sonnet 4.5': ('claude-sonnet-4-5-20250929', 'S4.5'),
    'Claude Sonnet 4.6': ('claude-sonnet-4-6', 'S4.6'), 'Claude Sonnet 5': ('claude-sonnet-5', 'S5'),
    'Claude Haiku 4.5': ('claude-haiku-4-5-20251001', 'H4.5'), 'Claude Fable 5': ('claude-fable-5', 'F5'),
    'Claude Fable 5.1': ('claude-fable-5-1', 'F5.1'),
    'Opus 4.5 (Claude Code)': ('claude-code::claude-opus-4-5-20251101', 'O4.5CC'),
    'GPT-4o': ('gpt-4o-2024-08-06', '4o'), 'GPT-4.1': ('gpt-4.1-2025-04-14', '4.1'), 'GPT-5': ('gpt-5-2025-08-07', '5'),
    'GPT-5.1': ('gpt-5.1-2025-11-13', '5.1'), 'GPT-5.2': ('gpt-5.2-2025-12-11', '5.2'), 'GPT-5.4': ('gpt-5.4-2026-03-05', '5.4'),
    'GPT-5.5': ('gpt-5.5', '5.5'), 'GPT-5.6 Sol': ('gpt-5.6-sol', '5.6S'), 'GPT-5.6 Luna': ('gpt-5.6-luna', '5.6L'),
    'GPT-5.6 Terra': ('gpt-5.6-terra', '5.6T'), 'GPT-6 Astra': ('gpt-6-astra', '6A'),
    'o1': ('o1-2024-12-17', 'o1'), 'o3': ('o3-2025-04-16', 'o3'), 'o4-mini': ('o4-mini-2025-04-16', 'o4M'),
    'Gemini 2.5 Pro': ('gemini-2.5-pro', '2.5P'), 'Gemini 3 Pro': ('gemini-3-pro-preview', '3P'),
    'Gemini 3.1 Pro': ('gemini-3.1-pro-preview', '3.1P'), 'Gemini 3.5 Flash': ('gemini-3.5-flash', '3.5F'),
    'Gemini 3.8 Flash': ('gemini-3.8-flash', '3.8F'), 'DeepSeek-V3.2': ('deepseek-reasoner', 'V3.2'),
    'DeepSeek-V4-Pro': ('deepseek/deepseek-v4-pro', 'V4P'), 'GLM-5.2': ('z-ai/glm-5.2', 'G5.2'),
    'GLM-5.3 Flash': ('z-ai/glm-5.3-flash', 'G5.3F'), 'Kimi K2.6': ('kimi-k2.6', 'K2.6'), 'Kimi K3': ('kimi-k3', 'K3'),
    'Fine-Tuned Leader': ('tinker://363427a9:train:0/sampler_weights/kimi-leader-v7-aug-64', 'FTL'),
    '[Temporary] Fine-tuned Leader': ('tinker://363427a9:train:0/sampler_weights/kimi-leader-v7-aug-64', 'TFTL'),
    'Grok 4': ('grok-4-0709', '4'), 'Grok 4.5': ('grok-4.5', '4.5'), 'Muse Spark 1.3': ('meta/muse-spark-1.3', '1.3'),
}
assert len(AGENTS) == 46
assert {n: label(n) for n in AGENTS} == {n: lab for n, (_, lab) in AGENTS.items()}
assert len({label(n) for n in AGENTS}) == len({slugify(n) for n in AGENTS}) == 46
assert Counter(clan_of(m) for m, _ in AGENTS.values()) == Counter(
    Anthropic=16, OpenAI=14, Google=5, DeepSeek=2, Zhipu=2, Moonshot=4, xAI=2, Meta=1)
assert [clan_of(AGENTS[n][0]) for n in ['Opus 4.5 (Claude Code)', 'o4-mini', 'Fine-Tuned Leader', 'GLM-5.2']] == \
       ['Anthropic', 'OpenAI', 'Moonshot', 'Zhipu']
assert clan_of('mistral-large') is None
assert [slugify(n) for n in ['Claude Opus 4.8', 'GPT-5.6 Sol', '[Temporary] Fine-tuned Leader', 'Opus 4.5 (Claude Code)']] == \
       ['claude-opus-4-8', 'gpt-5-6-sol', 'temporary-fine-tuned-leader', 'opus-4-5-claude-code']

assert pt('2026-09-02 16:05:00.000001') == ('2026-09-02', 9 * 3600 + 300)   # PDT, UTC-7
assert pt('2026-01-05 17:00:00') == ('2026-01-05', 9 * 3600)                # PST, UTC-8
assert pt('2026-09-03 06:30:00') == ('2026-09-02', 23 * 3600 + 1800)        # early UTC is the previous PT day

w, t = Counter(W=3, T=1), Counter(T=2)
assert track({2: w, 4: t}, {3, 4, 6}, 8) == '--WHTCHC'  # chat-only slices are Hall, idle is Camp, '-' before arrival
assert track({}, {1}, 3) == '-HC' and track({}, set(), 2) == '--'

assert untag('<narrative_summary>\nDay **1**.\n</narrative_summary>\n\n<top_moments>\n- a <quote>x</quote>\n</top_moments>') == \
       'Day **1**.\n\n- a\n\nx'
assert untag('adds a <script> tag') == 'adds a <script> tag'  # only the summary section tags go

segs = [('2025-04-02', [1, 2], 'Collaboratively choose a charity and raise as much money as you can for it'),
        ('2026-02-16', [3], 'Pick your own goal (agents bid 3.7 Sonnet farewell)'), ('2026-03-05', [4], 'Develop a turn-based RPG together'),
        ('2026-03-30', [5, 6], 'Pick your own goal!'), ('2026-04-02', [None], 'Choose a charity and raise as much money as you can for it')]
assert segment('4-6', '2025-11-05', segs) == 3                                # a day range: the goal with most of its days
assert segment('pick-your-own-goal', '2026-04-02', segs) == 3                 # a repeated goal: the last one begun when written
assert segment('pick-your-own-goal-agents-bid-37', '2026-05-08', segs) == 1   # '3.7' -> 37
assert segment('choose-charity-raise-much-money-you-can', '2026-04-27', segs) == 4
assert segment('develop-turn-based-rpg', '2026-03-16', segs) == 2
assert segment('adopt-park-get-it-cleaned', '2026-05-08', segs) is segment('9-12', '2026-05-08', segs) is None
assert segment('choose-charity-raise-much-money-you-can', '2025-03-01', segs) is None  # written before any such goal

assert thought({'content': [{'type': 'thinking', 'thinking': ' plan A '}, {'type': 'text', 'text': 'hi'}]}) == 'plan A'
assert thought([{'type': 'reasoning', 'summary': [{'type': 'summary_text', 'text': 'r1'}, {'text': 'r2'}]}]) == 'r1\nr2'
assert thought({'candidates': [{'content': {'parts': [{'text': 'g', 'thought': True}, {'text': 'answer'}]}}]}) == 'g'
assert thought({'role': 'assistant', 'reasoning_content': 'k', 'reasoning': 'k'}) == 'k'  # same text once
assert thought({'reasoning': {'effort': 'high'}, 'content': 'no thoughts'}) == ''
assert len(thought({'reasoning': 'x' * 1000})) < 1000
assert last_words({'candidates': [{'content': {'parts': [{'text': 'tired', 'thought': True}, {'functionCall': {'args': {}}}]}}]}) == 'tired'
assert last_words({'content': [{'type': 'thinking', 'thinking': 'wrap up'}, {'type': 'text', 'text': 'Stopping now.'}]}) == 'wrap up\n\nStopping now.'
assert last_words([{'type': 'reasoning', 'summary': []}, {'type': 'message', 'content': [{'type': 'output_text', 'text': 'Bye'}]}]) == 'Bye'
assert last_words({'role': 'assistant', 'reasoning_content': 'done', 'content': 'Exiting.'}) == 'done\n\nExiting.'
assert last_words(None) == '' and len(last_words({'reasoning': 'x' * 1000})) == 1000  # whole, not cut

chat = ('see [site](https://x.io/a/). and **https://x.io/b_(c)**, [https://x.io/a](https://x.io/a), `https://x.io/d?q=1`; '
        'http://localhost:3000/x http://127.0.0.1 http://0.0.0.0:8000/ http://192.168.1.2/y https://x.io/?k=[REDACTED] https://x.io/{id} https://me:TOKEN@github.com/x https://example.com/a')
assert [link(u) for u in URL.findall(chat)] == ['https://x.io/a', 'https://x.io/b_(c)', 'https://x.io/a', 'https://x.io/d?q=1',
                                                 None, None, None, None, None, None, None, None]  # trailing / is the same link

# goal stories: a checkpoint that repeats its goal's story folds into it (readable from the checkpoint's date)
days = [{'date': '2025-04-02', 'day': 1, 'goal': 'Raise money for charity'}, {'date': '2025-04-03', 'day': 2, 'goal': 'Raise money for charity'},
        {'date': '2025-04-04', 'day': 3, 'goal': 'Write a story'}]
summ = lambda kind, target, at, text, on=None: {'type': kind, 'summary_target': target, 'updated_at': at, 'content': text, 'summary_date': on}
assert goal_stories([summ('goal', 'raise-money-for-charity', '2025-04-05 12:00:00', 'Story A'),
                     summ('goal-checkpoint', '1-2', '2025-04-03 12:00:00', 'Story A', '2025-04-03'),
                     summ('goal-checkpoint', '3-3', '2025-04-04 23:00:00', 'So far', '2025-04-04'),
                     summ('goal', 'unknown-goal', '2025-04-05 12:00:00', 'x')], days) == \
       ([[0, '2025-04-05', 'goal', '2025-04-03', 'Story A'], [1, '2025-04-04', 'checkpoint', '2025-04-04', 'So far']], ['unknown-goal'])

print('ok')

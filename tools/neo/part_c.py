# -*- coding: utf-8 -*-
"""Доперевод строк, для которых в готовом переводе не нашлось пары.

Каждая запись: (файл в work/new/source, подстрока для поиска строки, русский
текст). Полная английская строка берётся из исходника, поэтому опечатки в ключе
невозможны. Сборка карты — work/neo/build_map.py.
"""

OVERRIDES = [
    ('scenes/events/afa_formed.scene.dry',
     'Remain silent with regards to the mass organization',
     'Промолчать насчёт этой массовой организации'),

    ('scenes/events/cvp_coalition_joever.scene.dry',
     'They cannot call a vote of no confidence due to the constitutional reforms',
     'Из-за конституционных реформ они не могут вынести вотум недоверия, но будут '
     'мешать нашему правительству при любой возможности.'),
    ('scenes/events/cvp_coalition_joever.scene.dry',
     'We have a majority without them.',
     'У нас есть большинство и без них.'),
    ('scenes/events/cvp_coalition_joever.scene.dry',
     'We have been effectively made a minority government',
     'Фактически нас превратили в правительство меньшинства, и '
     '<span style="color: #000000;">**[+ z_party_name +]**</span> намерена мешать '
     'нашим попыткам проводить политику.'),
    ('scenes/events/cvp_coalition_joever.scene.dry',
     'We were so kind.',
     'А мы были так любезны.'),

    ('scenes/events/death_of_hindenburg_president.scene.dry',
     'Kurt Schumacher is an ambitious rising star in the party',
     'Шумахер — амбициозная восходящая звезда партии, он более чем готов выставить '
     'свою кандидатуру. Он герой Великой войны, но его относительно молодой возраст '
     'тоже может сыграть роль.'),

    ('scenes/events/dvp_party_congress_0.scene.dry',
     'Stresemann maintains control of the party!',
     'Стреземан сохраняет контроль над партией!'),

    ('scenes/events/nazi_20.scene.dry',
     'Only the mighty can bear defeat.',
     'Лишь сильные способны вынести поражение.'),

    ('scenes/events/prussia_election_1928.scene.dry',
     'Braun is selected to be the Minister-President of Prussia.',
     'Браун избран министром-президентом Пруссии.'),

    ('scenes/events/workers_aid_unpopularity.scene.dry',
     'This will continue to be a problem if our popularity continues to flag.',
     'Это останется проблемой, если наша популярность продолжит падать.'),

    ('scenes/party_affairs/new_middle_consciousness.scene.dry',
     'No, we will not do this.',
     'Нет, мы этого не сделаем.'),
    ('scenes/party_affairs/new_middle_consciousness.scene.dry',
     'We will not do this.',
     'Мы этого не сделаем.'),
    ('scenes/party_affairs/rural_consciousness.scene.dry',
     'No, we will not do this.',
     'Нет, мы этого не сделаем.'),
    ('scenes/party_affairs/rural_consciousness.scene.dry',
     'We will not do this.',
     'Мы этого не сделаем.'),

    ('scenes/modinfo.scene.dry',
     'Other bug fixes.',
     'Прочие исправления ошибок.'),

    ('scenes/events/london_economic_conference.scene.dry',
     'administration. ?]',
     'Тем не менее мировая экономика медленно восстанавливается, отчасти благодаря '
     'экономическому стимулированию и более либеральной торговой политике '
     'администрации Рузвельта.'),
    ('scenes/events/london_economic_conference.scene.dry',
     'as well as our own economic plan',
     'Тем не менее мировая экономика медленно восстанавливается, отчасти благодаря '
     'экономическому стимулированию и более либеральной торговой политике '
     'администрации Рузвельта, а также нашему собственному экономическому плану.'),

    ('scenes/events/local_election_saxony.scene.dry',
     'Notable members of the',
     'Видные члены <span style="color: #fe9e00;">**ASPD**</span> — Макс Хельдт, Август '
     'Винниг (сторонник Капповского путча), Эрнст Никиш («<span style="color: #7A3C00;">'
     'национальный</span> <span style="color: #700000;">большевик</span>») и лидер партии, '
     'бывший министр-президент Вильгельм Бук. Партия была заклеймена как '
     '«<span style="color: #c00000;">социал</span>-<span style="color: #7A3C00;">фашистская</span>» '
     '<span style="color: #700000;">**коммунистами**</span>, что и стало '
     '<span class="tooltip-text" title="это я! создатель мода!">источником</span> этого термина.'),

    ('scenes/library.scene.dry',
     'Improve our relations with the',
     'Улучшить наши отношения с '
     '<span style="color: #750e0e;">Советским Союзом</span>.'),
    ('scenes/library.scene.dry',
     'and <span style="color: #3E88B3;">**Stahlhelm**</span>',
     'Запретить <span style="color: #7A3C00;">**СА**</span> и '
     '<span style="color: #3E88B3;">**Стальной Шлем**</span>.'),
    ('scenes/library.scene.dry',
     'Protect <span style="color: #700000;">communist</span> demonstrations',
     'Защитить <span style="color: #700000;">коммунистические</span> демонстрации.'),
    ('scenes/library.scene.dry', '<th>Party</th>', '<th>Партия</th>'),
    ('scenes/library.scene.dry', '<th>Workers</th>', '<th>Рабочие</th>'),
    ('scenes/library.scene.dry', '<th>New Middle Class</th>', '<th>Новый средний класс</th>'),
    ('scenes/library.scene.dry', '<th>Old Middle Class</th>', '<th>Старый средний класс</th>'),
    ('scenes/library.scene.dry', '<th>Rural</th>', '<th>Сельские жители</th>'),
    ('scenes/library.scene.dry', '<th>Unemployed</th>', '<th>Безработные</th>'),
    ('scenes/library.scene.dry', '<th>Catholics</th>', '<th>Католики</th>'),
]

# Эти строки остаются английскими осознанно (совпадает с готовым переводом
# или это не текст игры). См. docs/Нейронный доперевод.md.
KEPT_ENGLISH = [
    ('scenes/credits.scene.dry', 'библиография и ссылки на источники'),
    ('scenes/modinfo.scene.dry', 'библиография и ссылки на источники'),
    ('scenes/ending_slides.scene.dry', 'технические метки слайдов «Title: Subending …»'),
    ('scenes/events/election_1928.scene.dry', 'техническая метка «Title: …» варианта'),
    ('scenes/game_over.scene.dry', 'названия достижений (немецкие каламбуры)'),
]

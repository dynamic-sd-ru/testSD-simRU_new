import re, os

S1 = ('Они заявляют, что ожидают выполнения этих целей в течение [? if reichswehr_goal = 1 : месяцев.',
      'Они заявляют, что ожидают выполнения этих целей в течение [+ kpd_ultimatum_timer +] месяцев.')
S2 = ('Они заявляют, что ожидают выполнения этих целей в течение [? if interior_goal = 1 : месяцев.',
      'Они заявляют, что ожидают выполнения этих целей в течение [+ kpd_ultimatum_timer +] месяцев.')

SAX_NEW = ('Гинденбург назначает члена назначает [+ president +] <span style="color: #FFCC00;">**ЛНП**</span> [? if not lvp_formed:',
 '[+ president +] назначает [? if not lvp_formed: <span style="color: #C0A054;">**ННП**</span>?][? if lvp_formed: <span style="color: #FFCC00;">**ЛНП**</span>?] члена Вильгельма Бюнгера в качестве <i>рейхскомиссара</i> для управления Саксонией, которому поручено свернуть наши реформы и жестоко подавить <span style="color: #700000;">**RFB**</span>.')

ZR_SUB = ('subtitle: [? if in_weimar_coalition or in_grand_coalition or in_popular_front or (spd_prussia and not in_left_front_prussia and not in_spd_majority_prussia): <span style="color: #000000;">Партия Центра</span> в настоящее время состоит с нами в коалиции и не хочет ставить под угрозу её стабильность. [? if z_party_name != "ХНП": ?] Значительная часть <span style="color: #000000;">Партии Центра</span> поддерживает сохранение наших отношений и не хочет потенциально ставить их под угрозу. [? if z_party_name == "ХНП":',
 'subtitle: [? if in_weimar_coalition or in_grand_coalition or in_popular_front or (spd_prussia and not in_left_front_prussia and not sapd_toleration_prussia and not in_spd_majority_prussia): <span style="color: #000000;">Партия Центра</span> в настоящее время состоит с нами в коалиции и не хочет ставить под угрозу её стабильность. ?] [? if z_relation >= 40 and not (in_weimar_coalition or in_grand_coalition or in_popular_front or (spd_prussia and not in_left_front_prussia and not sapd_toleration_prussia and not in_spd_majority_prussia)): Значительная часть <span style="color: #000000;">Партии Центра</span> поддерживает сохранение наших отношений и не хочет потенциально ставить их под угрозу. ?]')

ZR_UNAVAIL = ('unavailable-subtitle: [? if not (in_weimar_coalition or in_grand_coalition or in_popular_front or (spd_prussia and not in_left_front_prussia and not in_spd_majority_prussia)): Мы не входим ни в какое правительство вместе с <span style="color: #000000;">Партией Центра</span>, что даёт им свободу действий.  [? if z_party_name != "ХНП": ?] Наш уровень отношений слишком низок, чтобы их волновало наше мнение. [? if z_party_name == "ХНП":',
 '[? if not (in_weimar_coalition or in_grand_coalition or in_popular_front or (spd_prussia and not in_left_front_prussia and not sapd_toleration_prussia and not in_spd_majority_prussia)): Мы не входим ни в какое правительство вместе с <span style="color: #000000;">Партией Центра</span>, что даёт им свободу действий. ?] [? if z_relation < 40 : Наш уровень отношений слишком низок, чтобы их волновало наше мнение. ?]')

HIND = ('Мы призываем [? if z_party_name != "ХНП": <span style="color: #000000;">Партию Центра</span> ?][? if z_party_name == "ХНП": <span style="color: #000000;">**ХНП**</span> ?]: им нужен [? if z_party_name != "ХНП":',
 'Мы призываем [? if z_party_name != "ХНП": <span style="color: #000000;">Партию Центра</span> ?][? if z_party_name == "ХНП": <span style="color: #000000;">**ХНП**</span> ?] поддержать [+ spd_candidate +] в качестве единого кандидата против <span style="color: #7A3C00;">фашизма</span>, утверждая, что вместе <span style="color: #000000;">Ве</span><span style="color: #DD0000;">йм</span><span style="color: #FFCC00;">ар</span>ская коалиция сможет победить <span style="color: #7A3C00;">нацистов</span>. [? if z_relation >= 50 : Мы также напоминаем им об истории сотрудничества между нашими партиями, которое началось ещё в 1918 году. ?]')

JOBS = {
 'scenes/events/kpd_goals.scene.dry': [S1],
 'scenes/events/kpd_goals_2.scene.dry': [S2],
 'scenes/events/saxony_reichsexekution_popular.scene.dry': [SAX_NEW],
 'scenes/events/z_right_party_congress.scene.dry': [ZR_SUB, ZR_UNAVAIL],
 'scenes/events/death_of_hindenburg_president.scene.dry': [HIND],
}

def repair_line(text, old, new):
    lines = text.split('\n')
    for i, ln in enumerate(lines):
        if ln.startswith(old):
            lines[i] = new
            return '\n'.join(lines), True
        if old.startswith(ln) and old.startswith('unavailable-subtitle'):
            pass
    return text, False

total = 0
for root in ('work/tr', 'work/tr2'):
    for rel, jobs in JOBS.items():
        p = os.path.join(root, rel)
        if not os.path.exists(p):
            continue
        text = open(p, encoding='utf-8').read()
        for old, new in jobs:
            text, ok = repair_line(text, old, new)
            if not ok and old.startswith('unavailable-subtitle:'):
                # line starts differently: replace the whole line containing it
                lines = text.split('\n')
                for i, ln in enumerate(lines):
                    if ln.startswith('unavailable-subtitle:') and 'z_relation' not in ln and 'свободу действий' in ln:
                        lines[i] = new
                        ok = True
                        break
                text = '\n'.join(lines)
            if ok:
                total += 1
            else:
                print('NOT FOUND in', p, ':', old[:60])
        open(p, 'w', encoding='utf-8').write(text)
print('repairs applied:', total)

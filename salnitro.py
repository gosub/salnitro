import random
from os import system

# TODO: remove exhaustion after turn end
# TODO: draw cards in player field
# TODO: max_field_size in game
# TODO: respect max_field_size when card played
# TODO: draw player along all 80 chars
# TODO: draw hand centered in 80 chars
# TODO: add attack function
# TODO: add attack command to interactive
# TODO: increase Burnout damage for every card not drawn

def mkplayer(name):
    deck = mkdeck()
    random.shuffle(deck)
    return {'name': name, 'health': 30, 'mana_slots': 0, 'mana': 0,
            'field': [], 'deck': deck, 'hand':[], 'discard':[]}

def mkdeck():
    values = [0,0,1,1,2,2,2,3,3,3,3,4,4,4,5,5,6,6,7,8]
    cards = [mk_damage_card, mk_heal_card, mk_minion_card]
    deck = [random.choice(cards)(v) for v in values]
    return deck

def mk_minion_card(cost):
    if cost == 0:
        attack, health = 0, 1
    else:
        deviation = random.choice(range(-1,2))
        attack, health = cost+deviation, cost-deviation
    return {'type': 'minion', 'name': 'minion',
            'cost': cost, 'attack': attack, 'health': health}

def mk_damage_card(cost):
    return {'type': 'spell', 'cost': cost, 'damage': cost,
            'fx': lambda self, game: decr_health(ask_target(game), self['damage']),
            'txt': "deal %d damage" % (cost)}

def mk_heal_card(cost):
    return {'type': 'spell', 'cost': cost, 'healing': cost,
            'fx': lambda self, game: incr_health(ask_target(game), self['healing']),
            'txt': "heal %d life" % (cost)}

def mkgame():
    return {'players': [mkplayer('P1'), mkplayer('P2')], 'active': random.choice([0,1]),
            'msg': [], 'max_hand_size': 5}

def active(game):
    return game['players'][game['active']]

def inactive(game):
    return game['players'][(game['active']+1)%2]

def switch_player(game):
    game['active'] = (game['active']+1)%2

def inc_mana_slot(player):
    player['mana_slots'] = min(10, player['mana_slots']+1)

def refill_mana(player):
    player['mana'] = player['mana_slots']

def incr_health(player, amount):
    player['health'] = min(30, player['health'] + amount)

def decr_health(player, amount):
    player['health'] -= amount
    assert player['health'] > 0, "%s lost" % (player['name'])

def draw(game, player):
    try:
        card = player['deck'].pop()
        if len(player['hand']) < game['max_hand_size']:
            player['hand'].append(card)
        else:
            game['msg'].append("hand full - card discarded")
            player['discard'].append(card)
    except IndexError:
        decr_health(player, 1)
        game['msg'].append("no more cards - burnout")

def play(g, hand_pos):
    player = active(g)
    card = player['hand'][hand_pos]
    if card['cost'] <= player['mana']:
        del player['hand'][hand_pos]
        player['mana'] -= card['cost']
        if card['type'] == 'spell':
            card['fx'](card, g)
            player['discard'].append(card)
        elif card['type'] == 'minion':
            card['exhausted'] = True
            player['field'].append(card)
        else:
            raise Exception('unknow card type %s' % (card['type']))
    else:
        g['msg'].append("insufficient mana")

def new_turn(game):
    switch_player(game)
    inc_mana_slot(active(game))
    refill_mana(active(game))
    draw(game, active(game))

def remove_exhaustion(player):
    for card in player['field']:
        if 'exhausted' in card:
            del card['exhausted']

def repr_mana(p):
    mana = "♦" * p['mana']
    mana += "♢" * (p['mana_slots'] - p['mana'])
    mana += "." * (10-p['mana_slots'])
    return mana

def repr_card(c, antagonist=False):
    if antagonist:
        return "[------]"
    elif c['type'] == 'spell':
        return "[[%d] %s]" % (c['cost'], c['txt'])
    elif c['type'] == 'minion':
        return "[[%d] %s %s[%d/%d]]" % (c['cost'], c['name'],
                    'zZzZ' if 'exhausted' in c and c['exhausted'] else '',
                    c['attack'], c['health'])
    else:
        raise Exception('unknow card type %s' % (c['type']))

def repr_hand(p, antagonist=False):
    return "\n".join(" "*n + repr_card(c, antagonist) for n, c in enumerate(p['hand']))

def repr_player(p, antagonist=False):
    hand = repr_hand(p, antagonist)
    health_mana = "%s  ❤️%2d  %s  ≣%d  ♲%d" % (p['name'], p['health'], repr_mana(p), len(p['deck']), len(p['discard']))
    lines = [hand, "", health_mana]
    if antagonist:
        lines.reverse()
    return "\n".join(lines)

def show(game):
    print(repr_player(inactive(game), True))
    print()
    print('+'*80)
    print()
    print(repr_player(active(game)))
    if game['msg']:
        print("\n".join(game['msg']))
        game['msg'] = []

def ask_target(game):
    tgts = [inactive(game), active(game)]
    print("targets:\n  %s" % "\n  ".join(str(idx+1) + ")" + tgt['name'] for idx, tgt in enumerate(tgts)))
    n = input('[RET=1]: ').lower().strip()
    if n == '':
        return tgts[0]
    else:
        return tgts[int(n)-1]

def interactive():
    g = mkgame()
    while True:
        new_turn(g)
        while True:
            system('clear')
            show(g)
            cmd = input('\ncard to play [RET=pass]: ').strip().lower()
            if cmd == '' or cmd == 'pass':
                break
            elif cmd == 'q' or cmd == 'quit':
                exit()
            elif all(x.isdigit() for x in cmd):
                try:
                    play(g, int(cmd))
                except IndexError:
                    pass
            else:
                print("command not recognized")


if __name__ == "__main__":
    interactive()

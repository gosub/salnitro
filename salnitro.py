import random
from os import system, get_terminal_size

# TODO: add attack function
# TODO: add attack command to interactive

def mkplayer(name):
    deck = mkdeck()
    random.shuffle(deck)
    return {'name': name, 'health': 30, 'mana_slots': 0, 'mana': 0,
            'field': [], 'deck': deck, 'hand':[], 'discard':[],
            'damage': 0, 'burnout': 1, 'type': 'player'}

def mkdeck():
    values = [0,0,1,1,2,2,2,3,3,3,3,4,4,4,5,5,6,6,7,8]
    cards = [mk_damage_card, mk_heal_card, mk_minion_card]
    deck = [random.choice(cards)(v) for v in values]
    return deck

def mk_minion_card(cost):
    if cost == 0:
        attack, health = 0, 1
    elif cost == 1:
        deviation = random.choice(range(-1,1))
        attack, health = cost+deviation, cost-deviation
    else:
        deviation = random.choice(range(-1,2))
        attack, health = cost+deviation, cost-deviation
    return {'type': 'minion', 'name': 'minion',
            'cost': cost, 'attack': attack, 'health': health,
            'damage': 0}

def mk_damage_card(cost):
    return {'type': 'spell', 'cost': cost, 'damage': cost,
            'fx': lambda self, game: deal_damage(game, ask_target(game), self['damage']),
            'txt': "deal %d damage" % (cost)}

def mk_heal_card(cost):
    return {'type': 'spell', 'cost': cost, 'healing': cost,
            'fx': lambda self, game: heal(ask_target(game), self['healing']),
            'txt': "heal %d life" % (cost)}

def mkgame():
    return {'players': [mkplayer('P1'), mkplayer('P2')], 'active': random.choice([0,1]),
            'msg': [], 'max_hand_size': 5, 'max_field_size': 3}

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

def heal(target, amount):
    target['damage'] = max(0, target['damage'] - amount)

def deal_damage(game, target, amount):
    target['damage'] += amount
    if target['health'] - target['damage'] <= 0:
        if target['type'] == 'player':
            raise Dead(target)
        elif target['type'] == 'minion':
            kill_minion(game, target)

def kill_minion(game, minion):
    for player in game['players']:
        try:
            position = list(id(c) for c in player['field']).index(id(minion))
            card = player['field'][position]
            del player['field'][position]
            player['discard'].append(card)
        except ValueError:
            pass

class Dead(Exception):
    pass

class NotEnoughMana(Exception):
    pass

class HandMaxxed(Exception):
    pass

class FieldMaxxed(Exception):
    pass

class EmptyDeck(Exception):
    pass

def draw(game, player):
    try:
        if len(player['deck']) <= 0:
            raise EmptyDeck
        card = player['deck'].pop()
        if len(player['hand']) >= game['max_hand_size']:
            raise HandMaxxed
        player['hand'].append(card)
    except HandMaxxed:
            game['msg'].append("hand full - card discarded")
            player['discard'].append(card)
    except EmptyDeck:
        game['msg'].append("no more cards - burnout -%d" % player['burnout'])
        deal_damage(game, player, player['burnout'])
        player['burnout'] += 1

def play(g, hand_pos):
    player = active(g)
    card = player['hand'][hand_pos]
    typ = card['type']
    try:
        if card['cost'] > player['mana']:
            raise NotEnoughMana
        if typ == 'minion' and len(player['field']) >= g['max_field_size']:
            raise FieldMaxxed
        player['mana'] -= card['cost']
        del player['hand'][hand_pos]
        if typ == 'spell':
            play_spell(g, player, card)
        elif typ == 'minion':
            play_minion(g, player, card)
        else:
            raise Exception('unknow card type %s' % (card['type']))
    except NotEnoughMana:
        g['msg'].append("insufficient mana")
    except FieldMaxxed:
        g['msg'].append("field is full")

def play_spell(g, player, card):
    card['fx'](card, g)
    player['discard'].append(card)

def play_minion(g, player, card):
    card['exhausted'] = True
    player['field'].append(card)

def new_turn(game):
    switch_player(game)
    inc_mana_slot(active(game))
    refill_mana(active(game))
    draw(game, active(game))

def end_turn(game):
    player = active(game)
    remove_exhaustion(player)

def remove_exhaustion(player):
    for card in player['field']:
        if 'exhausted' in card:
            del card['exhausted']

def repr_mana(p):
    txt = "%d/%d " % (p['mana'], p['mana_slots'])
    mana = "♦" * p['mana']
    mana += "♢" * (p['mana_slots'] - p['mana'])
    mana += "." * (10-p['mana_slots'])
    return txt + mana

def repr_card(c, antagonist=False):
    if antagonist:
        return "[------]"
    elif c['type'] == 'spell':
        return "[[%d] %s]" % (c['cost'], c['txt'])
    elif c['type'] == 'minion':
        return "[[%d] %s %s[%d/%d]]" % (c['cost'], c['name'],
                    'zZzZ' if 'exhausted' in c and c['exhausted'] else '',
                    c['attack'], c['health']-c['damage'])
    else:
        raise Exception('unknow card type %s' % (c['type']))

def repr_field(p, antagonist):
    return "  ".join(repr_card(c, antagonist) for c in p['field']).center(width())

def repr_hand(p, antagonist=False):
    cards = [repr_card(c, antagonist) for c in p['hand']]
    indented = [" "*n + c for n,c in enumerate(cards)]
    left_align = (width()-10)//2
    return "\n".join(" "*left_align + c for c in indented)

def repr_status(p, antagonist):
    name = p['name']
    health = "❤️" + str(p['health']-p['damage'])
    mana = repr_mana(p)
    deck_size = "≣" + str(len(p['deck']))
    discard_size = "♲" + str(len(p['discard']))
    return (" "*4).join([name, health, mana, deck_size, discard_size]).center(width())

def repr_player(p, antagonist=False):
    field = repr_field(p, False)
    hand = repr_hand(p, antagonist)
    bar = repr_status(p, antagonist)
    empty = ""
    lines = [field, empty, empty, hand, empty, bar]
    if antagonist:
        lines.reverse()
    return "\n".join(lines)

def width():
   return get_terminal_size().columns

def show(game):
    print(repr_player(inactive(game), True))
    print()
    print('+'*width())
    print()
    print(repr_player(active(game)))
    if game['msg']:
        print("\n".join(game['msg']))
        game['msg'] = []

def ask_target(game):
    def tgt_repr(t):
        if t['type'] == 'player':
            return t['name']
        elif t['type'] == 'minion':
            return repr_card(t)
    tgts = [inactive(game)]
    tgts += [m for m in inactive(game)['field'] if m['type']=='minion']
    tgts.append(active(game))
    tgts += [m for m in active(game)['field'] if m['type']=='minion']
    print("targets:")
    print("\n".join(str(idx+1) + ") " + tgt_repr(tgt) for idx, tgt in enumerate(tgts)))
    n = input('[RET=1]: ').lower().strip()
    if n == '':
        return tgts[0]
    else:
        return tgts[int(n)-1]

def interactive():
    g = mkgame()
    try:
        while True:
            new_turn(g)
            while True:
                system('clear')
                show(g)
                cmd = input('\ncard to play [RET=pass]: ').strip().lower()
                if cmd == '' or cmd == 'pass':
                    end_turn(g)
                    break
                elif cmd == 'q' or cmd == 'quit':
                    exit()
                elif all(x.isdigit() for x in cmd):
                    try:
                        play(g, int(cmd)-1)
                    except IndexError:
                        pass
                else:
                    print("command not recognized")
    except Dead as d:
        player, = d.args
        print("player %s has lost" % player['name'])

if __name__ == "__main__":
    interactive()

import random
from os import system, get_terminal_size

# TODO: add card deviations to card_collection
# TODO: add find_card function (returns field and position)
# TODO: manage no target/abort action during card play (not attack)
# TODO: implement first real card

def mkplayer(name):
    deck = mkdeck()
    random.shuffle(deck)
    return {'name': name, 'health': 30, 'mana_slots': 0, 'mana': 0,
            'field': [], 'deck': deck, 'hand':[], 'discard':[],
            'damage': 0, 'burnout': 1, 'type': 'player'}

def card_collection():
    all_cards = []
    all_cards += [mk_damage_card(x) for x in range(1,11)]
    all_cards += [mk_heal_card(x) for x in range(1,11)]
    all_cards += [mk_minion_card(x) for x in range(0,11)]
    all_cards += [mk_draw_card(x) for x in range(1,4)]
    all_cards += [mk_discard_card(x) for x in range(1,4)]
    return all_cards

def cards_by_cost(cost):
    return list(filter(lambda c: c['cost'] == cost, card_collection()))

def mkdeck():
    values = [0,0,1,1,2,2,2,3,3,3,3,4,4,4,5,5,6,6,7,8]
    deck = [random.choice(cards_by_cost(cost)) for cost in values]
    return deck

def mk_minion_card(cost, deviation=None):
    if cost == 0:
        attack, health = 0, 1
    elif cost == 1:
        if deviation is None:
            deviation = random.choice(range(-1,1))
        attack, health = cost+deviation, cost-deviation
    else:
        if deviation is None:
            deviation = random.choice(range(-1,2))
        attack, health = cost+deviation, cost-deviation
    return {'type': 'minion', 'name': 'minion',
            'cost': cost, 'attack': attack, 'health': health,
            'damage': 0, 'max_attacks': 1, 'attacks_this_turn': 0}

def mk_damage_card(cost):
    return {'type': 'spell', 'cost': cost, 'damage': cost,
            'fx': lambda self, game: deal_damage(game, ask_target(game), self['damage']),
            'txt': "deal %d damage" % (cost)}

def mk_heal_card(cost):
    return {'type': 'spell', 'cost': cost, 'healing': cost,
            'fx': lambda self, game: heal(ask_target(game), self['healing']),
            'txt': "heal %d life" % (cost)}

def mk_draw_card(cost):
    return {'type': 'spell', 'cost': cost, 'drawing': cost,
            'fx': lambda self, game: [draw(game, active(game)) for x in range(self['drawing'])],
            'txt': "draw %d cards" % (cost)}

def mk_discard_card(cost):
    return {'type': 'spell', 'cost': cost, 'discards': cost,
            'fx': lambda self, game: [discard(game, inactive(game), random_hand_card(game, inactive(game))) for x in range(self['discards'])],
            'txt': "opponent discards %d cards" % (cost)}

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

def random_hand_card(game, player):
    if len(player['hand']) <= 0:
        return None
    else:
        return random.randint(0, len(player['hand'])-1)

def discard(game, player, hand_pos):
    if not hand_pos is None:
        card = player['hand'][hand_pos]
        del player['hand'][hand_pos]
        player['discard'].append(card)

def can_attack(entity):
    return entity['type'] == 'minion' \
        and not 'exhausted' in entity \
        and entity['attacks_this_turn'] < entity['max_attacks']

def can_defend(entity):
    return entity['type'] == 'minion'

def attack(game, attacker, defender):
    dmg1 = attacker['attack']
    if defender['type'] == 'minion':
        dmg2 = defender['attack']
        deal_damage(game, defender, dmg1)
        deal_damage(game, attacker, dmg2)
    elif defender['type'] == 'player':
        deal_damage(game, defender, dmg1)
    attacker['attacks_this_turn'] += 1

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
    reset_attack_count(player)

def remove_exhaustion(player):
    for card in player['field']:
        if 'exhausted' in card:
            del card['exhausted']

def reset_attack_count(player):
    for e in player['field']:
        e['attacks_this_turn'] = 0

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

def ask_target(game, subset=None):
    repr = {'player': lambda p: p['name'], 'minion': repr_card}
    filt = {'attacker': can_attack, 'defender': can_defend, None: lambda x: True}
    prompt = {'attacker': "select attacker:", 'defender': "select defender:",
        None: "select target:"}
    a = inactive(game)
    aaa = [m for m in a['field'] if filt[subset](m)]
    b = active(game)
    bbb = [m for m in b['field'] if filt[subset](m)]
    tgts = []
    if subset == 'attacker':
        tgts += bbb
    elif subset == 'defender':
        tgts.append(a)
        tgts += aaa
    else:
        tgts.append(a)
        tgts += aaa
        tgts.append(b)
        tgts += bbb
    if not tgts:
        return None
    print(prompt[subset])
    print("\n".join(str(idx+1) + ") " + repr[tgt['type']](tgt)
        for idx, tgt in enumerate(tgts)))
    n = input('[RET=1]: ').lower().strip()
    if n == '':
        return tgts[0]
    elif n == 'q' or n == 'quit':
        return None
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
                elif cmd == 'a' or cmd == 'attack':
                    att = ask_target(g, 'attacker')
                    defe = ask_target(g, 'defender')
                    if not att is None and not defe is None:
                        attack(g, att, defe)
                elif cmd == 'q' or cmd == 'quit':
                    exit()
                elif cmd == 'h' or cmd == 'help':
                    g['msg'] += ["", "1-%d - play card N from hand" % (g['max_hand_size']),
                                 "a - attack", "h - help", "q - quit", "RET - pass turn"]
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

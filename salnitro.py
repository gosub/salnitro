import random
from os import system

def mkplayer(name):
    cards = [0,0,1,1,2,2,2,3,3,3,3,4,4,4,5,5,6,6,7,8]
    deck = [mkcard(v) for v in cards]
    random.shuffle(deck)
    return {'name': name, 'health': 30, 'mana_slots': 0, 'mana': 0, 'deck': deck, 'hand':[]}

def mkcard(cost):
    return {'cost': cost, 'damage': cost}

def mkgame():
    return {'players': [mkplayer('P1'), mkplayer('P2')], 'active': random.choice([0,1])}

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

def draw(player):
    try:
        player['hand'].append(player['deck'].pop())
    except IndexError:
        player['health'] -= 1

def play_card(player, hand_pos, target):
    card = player['hand'][hand_pos]
    assert card['cost'] <= player['mana'], "insufficient mana"
    del player['hand'][hand_pos]
    player['mana'] -= card['cost']
    target['health'] -= card['damage']
    assert target['health'] > 0, "current player wins"

def play(g, hand_pos):
    play_card(active(g), hand_pos, inactive(g))

def new_turn(game):
    switch_player(game)
    inc_mana_slot(active(game))
    refill_mana(active(game))
    draw(active(game))

def repr_mana(p):
    mana = "♦" * p['mana']
    mana += "♢" * (p['mana_slots'] - p['mana'])
    mana += "." * (10-p['mana_slots'])
    return mana

def repr_card(c):
    return "{%d,%d}" % (c['cost'], c['damage'])

def repr_hand(p):
    return " ".join(repr_card(c) for c in p['hand'])

def repr_player(p, inverted=False):
    hand = repr_hand(p)
    health_mana = "[%s][❤️%2d][%s][≣%d]" % (p['name'], p['health'], repr_mana(p), len(p['deck']))
    lines = [hand, health_mana]
    if inverted:
        lines.reverse()
    return "\n".join(lines)

def show(game):
    print(repr_player(inactive(game), True))
    print()
    print(repr_player(active(game)))

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
            elif all(x.isdigit() for x in cmd):
                play(g, int(cmd))
            else:
                print("command not recognized")


if __name__ == "__main__":
    interactive()

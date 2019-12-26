-module(salnitro).
-compile(export_all).

player(Name, Class, Deck) ->
    #{name => Name, health => 30, mana_slots => 0, mana => 0, field => [],
      deck => Deck, hand => [], discard => [], damage => 0, burnout => 1,
      type => player, class => Class, power_used => 0, power_per_turn => 0,
      power_cost => 2, attacks_per_turn => 1, attacks_this_turn => 0}.

game(P1, P2) ->
    #{p1 => P1, p2 => P2,
      active => lists:nth(rand:uniform(2), [p1, p2])}.

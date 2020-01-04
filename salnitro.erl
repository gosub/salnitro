-module(salnitro).
-compile(export_all).

%% GENERATORS

player(Name, Class, Deck) ->
    #{name => Name, health => 30, mana_slots => 0, mana => 0, field => [],
      deck => Deck, hand => [], discard => [], damage => 0, burnout => 1,
      type => player, class => Class, power_used => 0, power_per_turn => 0,
      power_cost => 2, attacks_per_turn => 1, attacks_this_turn => 0}.

game(P1, P2) ->
    #{p1 => P1, p2 => P2,
      active => lists:nth(rand:uniform(2), [p1, p2])}.

card(Name, Type, Cost, Rest) when is_map(Rest) ->
    maps:merge(#{name => Name, type => Type, cost => Cost}, Rest).

minion(Name, Cost, Attack, Health) ->
    Minion = #{attack => Attack, health => Health, damage => 0,
	       attacks_per_turn => 1, attacks_this_turn => 0},
    card(Name, minion, Cost, Minion).

minion(Name, Cost, Attack, Health, Rest) when is_map(Rest) ->
    Minion = #{attack => Attack, health => Health, damage => 0,
	       attacks_per_turn => 1, attacks_this_turn => 0},
    card(Name, minion, Cost, maps:merge(Minion, Rest)).

%% HEROES

hero(hunter) ->
    #{power => fun(Game) -> deal_damage(inactive(Game), 2) end,
      desc => "Deal 2 damage to the enemy hero."}.

%% GAME FUNCTIONS

active(#{active := p1, p1 := Player}) -> Player;
active(#{active := p2, p2 := Player}) -> Player.

inactive(#{active := p1, p2 := Player}) -> Player;
inactive(#{active := p2, p1 := Player}) -> Player.

switch_player(#{active := p1} = Game) -> Game#{active := p2};
switch_player(#{active := p2} = Game) -> Game#{active := p1}.

inc_mana_slot(Player) ->
    maps:update_with(mana_slots, fun(Slots) -> Slots+1 end, Player).

refill_mana(#{mana_slots:=Slots}=Player) ->
    Player#{mana := Slots}.

heal(#{damage := Dmg}=Target, Amount) ->
    Target#{damage := max(0, Dmg-Amount)}.

deal_damage(#{armor := Armor}=Target, Amount) when Amount < Armor ->
    Target#{armor := Armor-Amount};
deal_damage(#{armor := Armor}=Target, Amount) when Amount == Armor ->
    maps:take(armor, Target);
deal_damage(#{armor := Armor}=Target, Amount) when Amount > Armor ->
    Residual = Amount - Armor,
    Unarmored = maps:without([armor], Target),
    deal_damage(Unarmored, Residual);
deal_damage(#{health := Health}=Target, Amount) when Amount < Health ->
    Target#{health := Health-Amount};
deal_damage(#{health := Health}=Target, Amount) when Amount >= Health ->
    Target#{health := 0, dead => true}.

gain_armor(#{armor := Armor}=Target, Amount) ->
    Target#{armor := Armor+Amount};
gain_armor(Target, Amount) ->
    Target#{armor => Amount}.

hero_power(#{class := Class}) ->
    #{power:=Power} = hero(Class),
    Power.

use_hero_power(Game) ->
    #{mana:=Mana, power_cost:=PowerCost, power_per_turn := PowXTurn,
      power_used:= PowUsd}=Player = active(Game),
    Power = hero_power(Player),
    use_hero_power_aux(Game, Power, Mana, PowerCost, PowXTurn, PowUsd, Player).

use_hero_power_aux(G, _, _, _, PowXTurn, PowUsd, _)
  when PowUsd >= PowXTurn ->
    G;
use_hero_power_aux(G, _, Mana, PwrCost, _, _, _)
  when PwrCost > Mana ->
    G;
use_hero_power_aux(G, Pwr, Mana, PwrCost, _, PowUsd, Player) ->
    G2 = put_active(G, Player#{mana:= Mana-PwrCost}),
    G3 = Pwr(G2),
    put_active(G3, Player#{power_used:=PowUsd+1}).

put_active(#{active:=p1}=Game, Player) ->
    Game#{p1:=Player};
put_active(#{active:=p2}=Game, Player) ->
    Game#{p2:=Player}.

put_inactive(#{active:=p1}=Game, Player) ->
    Game#{p2:=Player};
put_inactive(#{active:=p2}=Game, Player) ->
    Game#{p1:=Player}.

equip(#{equip:=_}=Player, Weapon) ->
    Player#{equip := Weapon};
equip(Player, Weapon) ->
    Player#{equip => Weapon}.

is_equipped(#{equip:=_}) ->
    true;
is_equipped(_) ->
    false.

remove_weapon(Player) ->
    maps:without([equip], Player).

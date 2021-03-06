Module K
========
This is a reference implementation of the matching logic theory $K$, which is a reflexive theory of matching logic. 
```{.maude .k}
fmod K is
  protecting STRING .
```
```{.maude .k}
  sort KString . subsort String < KString .
```
Matching logic sorts become element of the sort `KSort`.

```{.maude .k}
  sorts   KSort   KSortList .
  subsort KSort < KSortList .
  op .KSortList :                     -> KSortList         .
  op _,_        : KSortList KSortList -> KSortList [assoc] .
  op Ksort      : KString             -> KSort             .
```
```{.maude .k}
  var S S1 S2 : KSort     .
  var Ss      : KSortList .
```
```{.maude .k}
  eq .KSortList, Ss = Ss .
  eq Ss, .KSortList = Ss .
```
Matching logic symbols become element of the sort `KSymbol`. A matching logic symbol takes a string as its *name*, a list *argument sorts*, and a *return sort*.

```{.maude .k}
  sorts   KSymbol   KSymbolList .
  subsort KSymbol < KSymbolList .
  op  .KSymbolList :                         -> KSymbolList         .
  op  _,_          : KSymbolList KSymbolList -> KSymbolList [assoc] .
  op  Ksymbol      : String KSortList KSort  -> KSymbol             .
```

```{.maude .k}
  ---- Eqs that make .KSymbolList the identity of _,_:
  eq  .KSymbolList, L:KSymbolList = L:KSymbolList .
  eq  L:KSymbolList, .KSymbolList = L:KSymbolList .

  ---- Getters of KSymbol
  op  getArgSorts : KSymbol -> KSortList .
  op  getRntSort  : KSymbol -> KSort     .
  op  getArity    : KSymbol -> Nat       .

  var Str : String .

  eq  getArgSorts(Ksymbol(Str, Ss, S)) = Ss         .
  eq  getRntSort (Ksymbol(Str, Ss, S)) = S          .
  eq  getArity   (Ksymbol(Str, Ss, S)) = length(Ss) .

  ---- KPattern is the sort of matching logic patterns ----

  sorts   KPattern   KPatternList .
  subsort KPattern < KPatternList .

  op  .KPatternList :                           -> KPatternList         .
  op  _,_           : KPatternList KPatternList -> KPatternList [assoc] .

  var Ps : KPatternList .

  eq  .KPatternList, Ps = Ps .
  eq  Ps, .KPatternList = Ps .

  ---- KVariable is the sort of matching logic variables ----

  sorts   KVariable       KVariableList .
  subsort KVariable     < KVariableList .  
  subsort KVariable     < KPattern .
  subsort KVariableList < KPatternList .

  op  .KVariableList :                             -> KVariableList .
  op  _,_            : KVariableList KVariableList -> KVariableList [assoc] .

  vars P Q R : KPattern  .
  var  X Y Z : KVariable .
  var  Sigma : KSymbol   .

  var Xs : KVariableList .

  ---- Eqs that make .KVariableList the identity of KVariableList:
  eq  .KVariableList, Xs = Xs .
  eq  Xs, .KVariableList = Xs .

  ---- Delete an element from a list.

  op  delete : KVariable KVariableList -> KVariableList .

  eq  delete(Y, .KVariableList) = .KVariableList        .
  eq  delete(Y, (X, Xs))        = if   (Y == X)
                                  then delete(Y, Xs)
                                  else X, delete(Y, Xs)
                                  fi                    .

  ---- Constructors of KPattern:

  op  Kvariable    : String                 KSort -> KVariable . 
  op  Kapplication : KSymbol   KPatternList       -> KPattern  .
  op  Kand         : KPattern  KPattern     KSort -> KPattern  .
  op  Knot         : KPattern               KSort -> KPattern  .
  op  Kexists      : KVariable KPattern     KSort -> KPattern  .

  ---- Fresh Variable Generation and Substitution

  op  KfreshName  : KPatternList                    -> String   .
  op  Ksubstitute : KPattern KPattern KVariable     -> KPattern .
  op  Ksubstitute : KPatternList KPattern KVariable -> KPatternList .

  ---- Eqs that define Ksubstitute on KPatternList (map):
  eq  Ksubstitute((P, Ps), R, Z)
   =  Ksubstitute(P, R, Z), Ksubstitute(Ps, R, Z) .

  ---- Eqs that define Ksubstitute (the one for Kexists is nontrivial):

  eq  Ksubstitute(X, R, Z) 
   =  if (X == Z) 
      then R 
      else X 
      fi .

  eq  Ksubstitute(Kapplication(Sigma, Ps), R, Z)
   =  Kapplication(Sigma, Ksubstitute(Ps, R, Z)) .

  eq  Ksubstitute(Kand(P, Q, S), R, Z) 
   =  Kand(Ksubstitute(P, R, Z),
           Ksubstitute(Q, R, Z),
           S) .

  eq  Ksubstitute(Knot(P, S), R, Z)
   =  Knot(Ksubstitute(P, R, Z), S) .


  ----   Ksubst(Kexists(X, P), R, Z)
  ---- = Kexists(Y, Ksubst(Ksubst(P, Y, X), R, Z))
  ----   where Y is a fresh variable
  ----   that has the same sort as X. 

 ceq  Ksubstitute(Kexists(Kvariable(Name:String, S1), P, S2), R, Z)
   =  Kexists(Kvariable(FN:String, S1), 
              Ksubstitute(Ksubstitute(P, Kvariable(FN:String, S1), 
                                         Kvariable(Name:String, S1)),
                          R, Z),
              S2)
  if  FN:String := KfreshName(P, R, Z) . 

  ---- Get all free variables that appear in a list of patterns.

  op  KgetFvs : KPatternList -> KVariableList .

  eq  KgetFvs(.KPatternList)           = .KVariableList          .
  eq  KgetFvs(.KVariableList)          = .KVariableList          .
  eq  KgetFvs(P, Ps)                   = KgetFvs(P), KgetFvs(Ps) .

  eq  KgetFvs(X)                       = X                       .
  eq  KgetFvs(Kapplication(Sigma, Ps)) = KgetFvs(Ps)             .
  eq  KgetFvs(Kand(P, Q, S))           = KgetFvs(P, Q)           .
  eq  KgetFvs(Knot(P,    S))           = KgetFvs(P)              .
  eq  KgetFvs(Kexists(X, P, S))        = delete(X, KgetFvs(P))   .

endfm


quit

 ---- Variable patterns.

  sorts VarPattern VarPatternList . subsort VarPattern < VarPatternList .

  subsort VarPattern     < Pattern . 
  subsort VarPatternList < PatternList .

  op _,_ : VarPatternList VarPatternList -> VarPatternList [ctor assoc] .

  op #variable    : String     MLSort                    -> VarPattern [ctor] .
  op #and         : Pattern    Pattern                   -> Pattern    [ctor] .
  op #or          : Pattern    Pattern                   -> Pattern    [ctor] .
  op #not         : Pattern                              -> Pattern    [ctor] .
  op #top         : MLSort                               -> Pattern    [ctor] .
  op #bottom      : MLSort                               -> Pattern    [ctor] .
  op #implies     : Pattern    Pattern                   -> Pattern    [ctor] .
  op #iff         : Pattern    Pattern                   -> Pattern    [ctor] .
  op #exists      : VarPattern Pattern                   -> Pattern    [ctor] .
  op #forall      : VarPattern Pattern                   -> Pattern    [ctor] .
  op #application : Symbol     PatternList               -> Pattern    [ctor] .
  op #value       : String     MLSort                    -> Pattern    [ctor] .
  op #equals      : Pattern    Pattern     MLSort MLSort -> Pattern    [ctor] .
  op #contains    : Pattern    Pattern     MLSort MLSort -> Pattern    [ctor] .

  var P Q : Pattern . 

  ---- Delete an element from a list

  op delete : Pattern PatternList -> PatternList .

  eq delete(P, .PatternList) = .PatternList .
  eq delete(P, Q) = if P == Q then .PatternList else Q fi .
  eq delete(P, (Q, Ps)) 
   = if P == Q 
     then delete(P, Ps)
     else Q, delete(P, Ps)
     fi .

  ---- Delete duplicate elements in a list.
  ---- The one that appears the first will remain in the list.

  op deleteDuplicate : PatternList -> PatternList .

  eq deleteDuplicate(.PatternList) = .PatternList .
  eq deleteDuplicate(P) = P .
  eq deleteDuplicate(P, Ps) = P, deleteDuplicate(delete(P, Ps)) .

  ---- Collect free variables that appear in a pattern. 

  op getFvs : Pattern     -> VarPatternList . 

  ---- Collect free variables that appear in a list of patterns.

  op getFvs : PatternList -> VarPatternList . 

  var X : String . vars P1 P2 : Pattern .

  eq getFvs(.PatternList) = .PatternList .
  eq getFvs(P, Ps) = deleteDuplicate(getFvs(P), getFvs(Ps)) .

  eq getFvs(#variable(X,S)) = #variable(X,S) .
  eq getFvs(#and(P1, P2)) = deleteDuplicate(getFvs(P1), getFvs(P2)) .
  eq getFvs(#or(P1, P2)) = deleteDuplicate(getFvs(P1), getFvs(P2)) .
  eq getFvs(#not(P)) = getFvs(P) .
  eq getFvs(#top(S)) = .PatternList .
  eq getFvs(#bottom(S)) = .PatternList .
  eq getFvs(#implies(P1, P2)) = deleteDuplicate(getFvs(P1), getFvs(P2)) .
  eq getFvs(#iff(P1, P2)) = deleteDuplicate(getFvs(P1), getFvs(P2)) .
  eq getFvs(#exists(X, S, P)) = delete(#variable(X, S), getFvs(P)) .
  eq getFvs(#forall(X, S, P)) = delete(#variable(X, S), getFvs(P)) .
  eq getFvs(#application(Sigma:Symbol, Ps)) = getFvs(Ps) .
  eq getFvs(#value(ValueRepresentation:String, S)) = .PatternList .
  eq getFvs(#equals(P1, P2, S1, S2)) 
   = deleteDuplicate(getFvs(P1), getFvs(P2)) .
  eq getFvs(#contains(P1, P2, S1, S2)) 
   = deleteDuplicate(getFvs(P1), getFvs(P2)) .

endfm

quit

  ---- Well-Formedness and getSort ----

  op wellFormed : Pattern -> Bool .
  op wellFormed : PatternList -> Bool . ---- if all patterns are well-formed
  op getSort : Pattern -> [MLSort] .
  op getSortList : PatternList -> [MLSortList] .

  eq getSortList(.PatternList) = .MLSortList .
  eq getSortList(P) = getSort(P) .
  eq getSortList(P, Ps) = getSort(P), getSortList(Ps) .

  cmb getSort(P) : MLSort if wellFormed(P) .


  eq wellFormed(#variable(X, S)) = true .
  eq wellFormed(#and(P1, P2))
   = wellFormed(P1) and wellFormed(P2) and getSort(P1) == getSort(P2) .
  eq wellFormed(#or(P1, P2))
   = wellFormed(P1) and wellFormed(P2) and getSort(P1) == getSort(P2) .
  eq wellFormed(#not(P)) = wellFormed(P) .
  eq wellFormed(#top(S)) = true .
  eq wellFormed(#bottom(S)) = true .
  eq wellFormed(#implies(P1, P2))
   = wellFormed(P1) and wellFormed(P2) and getSort(P1) == getSort(P2) .
  eq wellFormed(#iff(P1, P2))
   = wellFormed(P1) and wellFormed(P2) and getSort(P1) == getSort(P2) .
  eq wellFormed(#exists(X, S, P)) = wellFormed(P) .
  eq wellFormed(#forall(X, S, P)) = wellFormed(P) .
  eq wellFormed(#application(#symbol(X, Ss, S), Ps))
   = getArgumentSorts(#symbol(X, Ss, S)) == getSortList(Ps) .
  eq wellFormed(#value(ValueRepresentation:String, S)) = true .
  eq wellFormed(#equals(P1, P2, S1, S2)) 
   = getSort(P1) == S1 and getSort(P2) == S1 .
  eq wellFormed(#contains(P1, P2, S1, S2)) 
   = getSort(P1) == S1 and getSort(P2) == S1 .
  eq wellFormed(P) = false [owise] .

  eq getSort(#variable(X, S)) = S .
  ceq getSort(#and(P1, P2)) = getSort(P1) if wellFormed(#and(P1, P2)) .
  ceq getSort(#or(P1, P2)) = getSort(P1) if wellFormed(#or(P1, P2)) .
  eq getSort(#not(P)) = getSort(P) .
  eq getSort(#top(S)) = S .
  eq getSort(#bottom(S)) = S .
  ceq getSort(#implies(P1, P2)) = getSort(P1) if wellFormed(#implies(P1, P2)) .
  ceq getSort(#iff(P1, P2)) = getSort(P1) if wellFormed(#iff(P1, P2)) .
  eq getSort(#exists(X, S, P)) = getSort(P) .
  eq getSort(#forall(X, S, P)) = getSort(P) .
  ceq getSort(#application(#symbol(X, Ss, S), Ps)) = S 
  if wellFormed(#application(#symbol(X, Ss, S), Ps)) .
  eq getSort(#value(ValueRepresentation:String, S)) = S .
  ceq getSort(#equals(P1, P2, S1, S2)) 
   = S2 if wellFormed(#equals(P1, P2, S1, S2)) .
  ceq getSort(#contains(P1, P2, S1, S2)) 
   = S2 if wellFormed(#contains(P1, P2, S1, S2)) .  



  ---- Fresh variable generation ----

  sort StringList . subsort String < StringList .
  op .StringList : -> StringList [ctor] .
  op _,_ : StringList StringList -> StringList [ctor assoc] .

  var Strs : StringList .

  eq .StringList, Strs = Strs .
  eq Strs, .StringList = Strs .

  ---- Generate (in a deterministic way) a fresh variable name 
  ---- that is not in the argument name list. 

  op freshName : StringList -> String .

  ---- Generate (in a deterministic way) a fresh variable name 
  ---- that does not occur free in the argument pattern list. 

  op freshName : PatternList -> String .

  op getName : VarPattern -> String .
  op getName : VarPatternList -> StringList .
  eq getName(#variable(X, S)) = X .
  eq getName(.PatternList) = .StringList .
  eq getName(P, Ps) = getName(P), getName(Ps) .

  eq freshName(Ps) = freshName(getName(getFvs(Ps))) .

  op cat : StringList -> String . 

  eq cat(.StringList) = "" .
  eq cat(X) = X .
  eq cat(X,Strs) = X + cat(Strs) .
  ---- Original fresh name
  ---- eq freshName(Strs) = cat(Strs) .

  ---- New way to build fresh name
  op makeName : String -> String .
  op getLetter : Nat -> Nat .

  var c1 c2 : Char . var n : Nat .
  eq getLetter(n) = if n < 141 and n > 132 then n + 6 else n fi .
  eq makeName("") = "" .
  eq makeName(c1) = c1 .
  eq makeName(X) 
   = cat(char((getLetter((ascii(substr(X,0,1)) * ascii(substr(X,0,1)) 
     + ascii(substr(X,1,1)) * ascii(substr(X,1,1)))) rem 58) + 65),
     makeName(substr(X,2,length(X)))) .

  eq freshName(Strs) = makeName(cat(Strs)) .

  ---- Substitution ----

  op subst : Pattern Pattern Pattern -> Pattern .
  op subst : PatternList Pattern Pattern -> PatternList .

  var R : Pattern . var V : String .

  eq subst(.PatternList, Q, R) = .PatternList .
  eq subst((P, Ps), Q, R) = subst(P, Q, R), subst(Ps, Q, R) .

  eq subst(R, Q, R) = Q .
  eq subst(#and(P1, P2), Q, R) = #and(subst(P1, Q, R), subst(P2, Q, R)) .
  eq subst(#or(P1, P2), Q, R) = #or(subst(P1, Q, R), subst(P2, Q, R)) .
  eq subst(#not(P), Q, R) = #not(subst(P, Q, R)) .
  eq subst(#top(S), Q, R) = #top(S) .
  eq subst(#bottom(S), Q, R) = #bottom(S) .
  eq subst(#implies(P1, P2), Q, R) 
   = #implies(subst(P1, Q, R), subst(P2, Q, R)) .
  eq subst(#iff(P1, P2), Q, R) = #iff(subst(P1, Q, R), subst(P2, Q, R)) .
  ceq subst(#exists(X, S, P), Q, R)
   = #exists(V, S, subst(subst(P, #variable(V, S), #variable(X, S)), Q, R))
  if V := freshName(P, Q, R) .
  ceq subst(#forall(X, S, P), Q, R)
   = #forall(V, S, subst(subst(P, #variable(V, S), #variable(X, S)), Q, R))
  if V := freshName(P, Q, R) .
  eq subst(#application(Sigma:Symbol, Ps), Q, R)
   = #application(Sigma:Symbol, subst(Ps, Q, R)) .
  eq subst(#value(ValueRepresentation:String, S), Q, R)
   = #value(ValueRepresentation:String, S) .
  eq subst(#equals(P1, P2, S1, S2), Q, R)
   = #equals(subst(P1, Q, R), subst(P2, Q, R), S1, S2) .
  eq subst(#contains(P1, P2, S1, S2), Q, R) 
   = #equals(subst(P1, Q, R), subst(P2, Q, R), S1, S2) .
  eq subst(P, Q, R) = P [owise] .


  ---- Matching logic theories

  sorts Signature Theory .

  op #signature : MLSortList SymbolList -> Signature [ctor] .
  op #theory : Signature PatternList -> Theory [ctor] .


---- Proof system ----

  sorts Goal GoalList . subsort Goal < GoalList .
  op .GoalList : -> GoalList [ctor] . 
  op __ : GoalList GoalList 
        -> GoalList [ctor assoc id: .GoalList format(d n d)] .
  op _|-_ : PatternList Pattern -> Goal [ctor] .

  sort Tactic .
endfm
```



```

```
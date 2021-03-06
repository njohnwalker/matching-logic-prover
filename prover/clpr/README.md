# The fixpoint prover.

# Todos
- [ ] finish `lr -> ll` example on paper.
- [ ] finish `ll * list -> list` example on paper.
- [ ] implement KT.
- [ ] make `ll -> lr` work.

# Instruction

All is in `fix.maude`. 
To run it, do
```
sudo apt install maude
maude fix.maude
```

To run `clpr` files:

```
./run-clpr test.clpr
```

# All in CLPR

## Main rules: (WRAP), (KT), (UNWRAP)

```
========   All proof rules for LFP (flag=false) =======
 (QE) Quantifier elimination
 (DP) Direct proof
 (PM) Pattern matching
(FIX) Right unfold only
(LFP) A compound rule
========   All proof rules for GFP (flag=true) =========
 (QE) Quantifier elimination
 (DP) Direct proof
 (PM) Pattern matching
(FIX) Left unfold only
(GFP) A compound rule
========== An application of LFP rule in the search tree =========
Given LHS |= RHS
Given P(y1,yn) ≡ B \/ ∃z1,zn: P(z1,zn)/\...
               ≡ B \/ R (for short)
foreach recursive predicate P on the lhs:
    (WRAP)             to have P |= ∃F:  F & floor(LHS[F/P] => RHS)
                               P |= G (for short)                                    
    (RIGHT-STRENGTHEN) to have P |= forall x1,xn: G   // Choose such x1,xn that after (QE) we have G
    (KT)               to have B \/ R[forall x1,xn: G / P] |= forall x1,xn: G
    (QE)               to have B \/ R[forall x1,xn: G / P] |= G
    (UNWRAP)           to have LHS[B \/ R[forall x1,xn: G / P] /P] |= RHS
    
    prove for all disjuncts on the lhs
```

## How to apply (KT) in CLPR syntax?

```
Given a proof obligation p(x) /\ LHS(x,y) -> RHS(x,y).
Here x and y are vectors of all free variables that appear in p and LHS.
We have p is a recursive predicate, and LHS is the rest of the left-hand side.
LHS might be empty, in which case it's considered as a "true". 

What's important is that here all formulas are in fact FOL formulas (either true or false).
In other words, they are predicate patterns in matching logic (either the empty set or the total set).
This greatly simplifies the application of KT. In particular, it simplifies (Plugin) and (Plugout) A LOT.

Given the definition of p:
  p(x) ≡ ... \/ (exists z . BODY(x,z) /\ p(z)) \/ ....
Here z is a vector of all free variables that occur in p on the right-hand side,
and BODY is the body of a case of the recursive definitino of p,
excluding the recursive occurrence of p itself.
Notice that x and z may not be disjoint. Also we assume p occurs at most once
in each case, but this assumption might not be important. 
The case where there is no occurrence of p is known as a base case. And applying
KT rule with those base cases are simple. Simply unfold. Done.

We focus on the non-base cases.

Here's how we apply KT rule in matching logic.

(1) p(x) /\ LHS(x,y) -> RHS(x,y)

/* (Plugout) and (Forall) */

(2) p(x) -> forall y . (LHS(x,y) -> RHS(x,y))

/* apply KT. */

(3) ... \/ exists z . BODY(x,z) /\ forall y . (LHS(z,y) -> RHS(z,y)) \/ ...
  -> forall y . (LHS(x,y) -> RHS(x,y))
  
/* this is just one case */

(4) exists z . BODY(x,z) /\ forall y . (LHS(z,y) -> RHS(z,y))
  -> forall y . (LHS(x,y) -> RHS(x,y))

/* (Plugin) and (UG).  We must pick a fresh z in the following. */

(5) BODY(x,z) /\ forall y . (LHS(z,y) -> RHS(z,y)) /\ LHS(x,y) -> RHS(x,y)

/* Let's rename the bound variable y to a fresh name t, to avoid confusion. */

(5) BODY(x,z) /\ forall t . (LHS(z,t) -> RHS(z,t)) /\ LHS(x,y) -> RHS(x,y)
```

### QUESTION: HOW TO DEAL WITH (5)?

The formula `forall t . (LHS(z,t) -> RHS(z,t))` in the above (5) is annoying.
Can we instead prove the following (6)?
Notice that if (6) holds, (5) must hold. But not vice versa.
Basically, we instantiate the `forall t` in (5) with a guess, the variable `y`,
which already occurs on LHS and RHS.

```
(6) BODY(x,z) /\ (LHS(z,y) -> RHS(z,y)) /\ LHS(x,y) -> RHS(x,y)
```

By simple propositional reasoning, we know that in order to prove (6), 
one should first try to prove
```
(6a) BODY(x,z) /\ LHS(x,y) -> RHS(x,y)
```
If (6a) is proved, then (6) must hold.
However, in many cases (my experience) (6a) is not provable. 

Then one should try to prove both:
```
(6b) BODY(x,z) /\ LHS(x,y) /\ RHS(z,y) -> RHS(x,y)
(6c) BODY(x,z) /\ LHS(x,y) -> LHS(z,y)
```

Let's summarize the above.

```
unfold(p(x),
  [
  ...
  /* variable vectors x and z may not be disjoint.
   * but new variables in z must be fresh.
   */
  body([p(z) | UNFOLDABLEBODY], NONUNFOLDABLEBODY) 
  ...
  ]).

append(UNFOLDABLEBODY, NONUNFOLDABLEBODY, BODY).

Here's our proof obligation.

(1) p(x) /\ LHS -> RHS

Applying KT on (1) means the follows.

Either prove:
(a) BODY /\ LHS -> RHS

Or prove both:
(b) BODY /\ LHS /\ RHS[z/x] -> RHS
(c) BODY /\ LHS -> LHS[z/x]
```


### Does it work?

No.

Let's take a look at the example `ll -> lr`.

```
Definition.

ll(H,X,Y,F) ≡
   X=Y /\ F=emptyset
\/ ll(H,T,Y,F1) /\ X>0 /\ X!=Y /\ T=H[X] /\ X notin F1 /\ F=F1+{X}

lr(H,X,Y,F) ≡
   X=Y /\ F=emptyset
\/ lr(H,X,T,F1) /\ Y>0 /\ X!=Y /\ Y=H[T] /\ T notin F1 /\ F=F1+{T}

Proof.

(1) ll(H,X,Y,F) -> lr(H,X,Y,F)

/* apply KT on ll(H,X,Y,F) */

/* ll has two cases. The base case is easy and omitted. Consider inductive case. */

/* Case is ll(H,X,Y,F) :- ll(H,T,Y,F1) /\ X>0 /\ X!=Y /\ T=H[X] /\ X notin F1 /\ F=F1+{X}
 * variable vector x is H X Y F
 * variable vector z is H T Y F1
 * BODY is X>0 /\ X!=Y /\ T=H[X] /\ X notin F1 /\ F=F1+{X}
 * LHS is nothing
 * RHS is lr(H,X,Y,F)
 * The renaming [z/x] is [T/X,F1/F]
 * LHS[z/x] is nothing
 * RHS[z/x] is lr(H,T,Y,F1)
 */

Let's try to prove both

BODY /\ LHS /\ RHS[z/x] -> RHS
(1b) X>0 /\ X!=Y /\ T=H[X] /\ X notin F1 /\ F=F1+{X} /\ lr(H,T,Y,F1) -> lr(H,X,Y,F)

BODY /\ LHS -> LHS[z/x]
(1c) X>0 /\ X!=Y /\ T=H[X] /\ X notin F1 /\ F=F1+{X} -> true

(1c) is proved immediately. Let's see (1b).

Restate (1b).

(1b) X>0 /\ X!=Y /\ T=H[X] /\ X notin F1 /\ F=F1+{X} /\ lr(H,T,Y,F1) -> lr(H,X,Y,F)

/* apply KT on lr(H,T,Y,F1) */

/* lr has two cases. The base case is easy and omitted. Consider inductive case. */

/* Case is lr(H,T,Y,F1) :- lr(H,T,T1,F2) /\ T>0 /\ T!=Y /\ Y=H[T1] /\ T1 notin F2 /\ F1=F2+{T1}
 * variable vector x is H,T,Y,F1
 * variable vector z is H,T,T1,F2
 * BODY is T>0 /\ T!=Y /\ Y=H[T1] /\ T1 notin F2 /\ F1=F2+{T1}
 * LHS is X>0 /\ X!=Y /\ T=H[X] /\ X notin F1 /\ F=F1+{X}
 * RHS is lr(H,X,Y,F)
 * The renaming [z/x] is [T1/Y,F2/F1]
 * LHS[z/x] is X>0 /\ X!=T1 /\ T=H[X] /\ X notin F2 /\ F=F2+{X}
 * RHS[z/x] is lr(H,X,T1,F)
 */

/* CAUTION!!! RHS[z/x] is unexpected and wrong, because F is the wrong footprint. Here's why.
 * (1b) basically says that 
 *   X|->T /\ lr(T,Y) -> lr(X,Y)
 * And lr(X,Y) has footprint F = F1 + {X}, and lr(T,Y) has footprint F1.
 * Applying (KT) we should get a new proof obligation
 *   X|->T /\ lr(X,T1) /\ T1|->T -> lr(X,Y)
 * which should be provable. 
 * Unfortunately, the footprint of lr(X,T1) is wrong. It's not F, but F\{T1} = F2+{X}.
 * The reason we get this wrong footprint is because we drop the "forall t" from (5). 
 * One can confirm that the above are not provable.
 * /
 
```

### Use an axiom set

We can use an axiom set to help us remember that
```
(5) BODY(x,z) /\ forall t . (LHS(z,t) -> RHS(z,t)) /\ LHS(x,y) -> RHS(x,y)
```

Here's how.

```
(1) p(x) /\ LHS -> RHS

apply KT.

add LHS[z/x,t/y] -> RHS[z/x,t/y] to the axiom set, where t is fresh (placeholder).
What's important is to remember the occurrence of z in LHS.

Then, with an axiom being added, we prove

(2) { AXIOMS } |- BODY /\ LHS -> RHS
```

Here's the example `ll->lr`.

```
Proof.

(1) ll(H,X,Y,F) -> lr(H,X,Y,F)

/* apply KT on ll(H,X,Y,F) */

/* ll has two cases. The base case is easy and omitted. Consider inductive case. */

/* Case is ll(H,X,Y,F) :- ll(H,T,Y,F1) /\ X>0 /\ X!=Y /\ T=H[X] /\ X notin F1 /\ F=F1+{X}
 * variable vector x is H X Y F
 * variable vector y is nothing
 * variable vector z is H T Y F1
 * variable vector t is nothing because y is nothing
 * the renaming [z/x,t/y] is [T/X,F1/F]
 * BODY is X>0 /\ X!=Y /\ T=H[X] /\ X notin F1 /\ F=F1+{X}
 * LHS is nothing
 * RHS is lr(H,X,Y,F)
 * LHS[z/x,t/y] is nothing
 * RHS[z/x,t/y] is lr(H,T,Y,F1)
 * the new axiom is true -> lr(H,T,Y,F1).
 */

{ AXIOMS } |- BODY /\ LHS -> RHS
(2) { true -> lr(H,T,Y,F1) } |-
    X>0 /\ X!=Y /\ T=H[X] /\ X notin F1 /\ F=F1+{X} -> lr(H,X,Y,F)
 
The axiom has no fresh variable (see above, t is nothing). In other words,
the universal quantification "forall t" has no effect, and the axiom has exactly
one instance: true -> lr(H,T,Y,F1).

This means that we can remove it from the axiom set, and just add it to the premise.

(3) X>0 /\ X!=Y /\ T=H[X] /\ X notin F1 /\ F=F1+{X} /\ (true -> lr(H,T,Y,F1)) -> lr(H,X,Y,F)

By simple propositional reasoning, this is just

(4) X>0 /\ X!=Y /\ T=H[X] /\ X notin F1 /\ F=F1+{X} /\ lr(H,T,Y,F1) -> lr(H,X,Y,F)

Now apply KT again. This time on lr(H,T,Y,F1). We care only about the inductive case.

/* Case is lr(H,T,Y,F1) :- lr(H,T,T1,F2) /\ T>0 /\ T!=Y /\ Y=H[T1] /\ T1 notin F2 /\ F1=F2+{T1}
 * variable vector x is H,T,Y,F1
 * variable vector y is X,F
 * variable vector z is H,T,T1,F2
 * variable vector t is X',F' because y is X,F
 * the renaming [z/x,t/y] is [T1/Y,F2/F1,X'/X,F'/F]
 * BODY is T>0 /\ T!=Y /\ Y=H[T1] /\ T1 notin F2 /\ F1=F2+{T1}
 * LHS is X>0 /\ X!=Y /\ T=H[X] /\ X notin F1 /\ F=F1+{X}
 * RHS is lr(H,X,Y,F)
 * LHS[z/x,t/y] is X'>0 /\ X'!=T1 /\ T=H[X'] /\ X' notin F2 /\ F'=F2+{X'}
 * RHS[z/x,t/y] is lr(H,X',T1,F')
 * the new axiom is X'>0 /\ X'!=T1 /\ T=H[X'] /\ X' notin F2 /\ F'=F2+{X'} -> lr(H,X',T1,F')
 */

{ AXIOMS } |- BODY /\ LHS -> RHS
(5) { X'>0 /\ X'!=T1 /\ T=H[X'] /\ X' notin F2 /\ F'=F2+{X'} -> lr(H,X',T1,F') } |-
    T>0 /\ T!=Y /\ Y=H[T1] /\ T1 notin F2 /\ F1=F2+{T1} 
    /\ X>0 /\ X!=Y /\ T=H[X] /\ X notin F1 /\ F=F1+{X}
 -> lr(H,X,Y,F)
 
Match! X' := X and F' := F2+{X} (HOW DO I KNOW?!?!)
Rename in AXIOMS X' to X'' and F' to F''.
Add X' and F' to the proof obligation, and two equations X'=X, F'=F2+{X}.

(6*){ X''>0 /\ X''!=T1 /\ T=H[X''] /\ X'' notin F2 /\ F''=F2+{X''} -> lr(H,X'',T1,F'') } |-
    T>0 /\ T!=Y /\ Y=H[T1] /\ T1 notin F2 /\ F1=F2+{T1} 
    /\ X>0 /\ X!=Y /\ T=H[X] /\ X notin F1 /\ F=F1+{X}
    /\ X'=X /\ F'=F2+{X}
    /\ (X'>0 /\ X'!=T1 /\ T=H[X'] /\ X' notin F2 /\ F'=F2+{X'} -> lr(H,X',T1,F')) /* axiom instance */
 -> lr(H,X,Y,F)

(6*) is not in CLPR syntax. Let's do some propositional reasoning and get rid of the implication.

(6*) has the form L /\ (AL -> AR) -> R, where AL -> AR is the axiom instance.
To prove (6*), it suffices to prove L -> AL and L /\ AR -> R.
This leads us to prove both:

(6a){ AXIOMS } |-
    T>0 /\ T!=Y /\ Y=H[T1] /\ T1 notin F2 /\ F1=F2+{T1} 
    /\ X>0 /\ X!=Y /\ T=H[X] /\ X notin F1 /\ F=F1+{X}
    /\ X'=X /\ F'=F2+{X}
 -> X'>0 /\ X'!=T1 /\ T=H[X'] /\ X' notin F2 /\ F'=F2+{X'}

(6b){ AXIOMS } |-
    T>0 /\ T!=Y /\ Y=H[T1] /\ T1 notin F2 /\ F1=F2+{T1} 
    /\ X>0 /\ X!=Y /\ T=H[X] /\ X notin F1 /\ F=F1+{X}
    /\ X'=X /\ F'=F2+{X}
    /\ lr(H,X',T1,F')
 -> lr(H,X,Y,F)

Now, (6a) is proved by a (DIRECT PROOF). (6b) is proved by a (RIGHT UNFOLD).
```

### Avoid an axiom set

Using axiom sets makes implementation more complex. To avoid that,
we here introduce a heuristic about how to instantiate the universally
quantified variables that appear in (5).
Heuristics are, of course, sound, but in general incomplete. 
We trade off completeness for simpler proof rules.

Again, let's look at (1) and (5).

```
(1) p(x)                                           /\ LHS(x,y) -> RHS(x,y)
(5) forall t . (LHS(z,t) -> RHS(z,t)) /\ BODY(x,z) /\ LHS(x,y) -> RHS(x,y)
```

The purpose of this section is to identity a partition of `t = t1 U t2`,
and instantiate the `forall t` by letting `t1` be fresh variables
and `t2` be `y2` (the subset of `y` corresponding to the subset `t1`).
The former is equivalent to change `forall t1` to `exists t1`, or simply
drop the `forall`. 
The reason why that works is `t1` is fully determined by the choice of `t2`
and other variables. Or at least we hope so.
So once we let `t2` be `y2`, the values of `t1` are fixed. 
Letting them be some fresh and free variables doesn't do any harm.
SMT solvers will find out their intended values.

We need to be more precise about variables. To be consistent, I'll stick to
the variables `x`, `y`, and `z` as above. 
Let's consider a case of the recursive definition.
```
p(x) === ... \/ exists z . p(z) /\ BODY(x,z)
```
As we point out, `x` and `z` may not be disjoint.
When we unfold `p(x)` according to one case,
we obtain `p(z)`, by changing variables in some positions to fresh variables,
and keep the rest unchanged. 
Let's call the positions where variables change the _critical positions_,
and the rest positions the _noncritical positions_. 
Therefore, `x` and `z` are only different on the critical positions of `p`,
and are the same on the noncritical positions.

Notice that critical positions may be different for different cases.

Let's consider the proof obligation

```
(1) p(x) /\ LHS(x,y) -> RHS(x,y)
```

Let's assume that `p` also occurs in `RHS(x,y)`, exactly once.
And let `y1` be the set of variables that are in `y` and also appear
on the critical positions of the recursive predicate `p` that occurs in `RHS(x,y)`.
Let `y2` be the set of remaining variables in `y`.
We obtain a partition: `y = y1 U y2`. 

Notice that the assumption that `p` occurs exactly once on `RHS(x,y)`
can be relaxed to that `p` occurs at most once.
Indeed, if `p` doesn't occur on `RHS(x,y)`, we let `y1` be empty and `y2` be
equal to `y`.

Now we state (5)

```
(5) forall t . (LHS(z,t) -> RHS(z,t)) /\ BODY(x,z) /\ LHS(x,y) -> RHS(x,y)
```

and we instantiate `forall t` by letting `t1` free and `t2` be `y2`.
And we get

```
(6) (LHS(z,t) -> RHS(z,t))[y2/t2] /\ BODY(x,z) /\ LHS(x,y) -> RHS(x,y)

Or equivalently,

(6') (LHS(z,y) -> RHS(z,y))[t1/y1] /\ BODY(x,z) /\ LHS(x,y) -> RHS(x,y)
```

Notice that `(LHS(z,y) -> RHS(z,y))[t1/y1]` is the result of
* Grab `LHS(z,y) -> RHS(z,y)`.
* Consider every variable `yi` in the set of variables `y`.
* If `yi` occurs in a critical position of `p` on `RHS(z,y)`, then rename it to a fresh variable `ti`.
* If `yi` occurs in a noncritical position of `p` on `RHS(z,y)`, or doesn't occur at all, then keep it.

Finally, by simple propositional reasoning, (6') is equivalent to
proving 

```
(6''), equivalent to (6').

PROVE BOTH:
(6a) BODY(x,z) /\ LHS(x,y) -> LHS(z,y)[t1/y1] \/ RHS(x,y)
(6b) RHS(z,y)[t1/y1] /\ BODY(x,z) /\ LHS(x,y) -> RHS(x,y)
```

(6a) has disjunction on the rhs. By simple propositional reasoning, 
we can show that in order to prove (6''), it is _sufficient_ to prove the following: 

```
EITHER BOTH
  (6a2) BODY(x,z) /\ LHS(x,y) -> LHS(z,y)[t1/y1]
  (6b) LHS(z,y)[t1/y1] /\ RHS(z,y)[t1/y1] /\ BODY(x,z) /\ LHS(x,y) -> RHS(x,y)
OR JUST
  (6a1) BODY(x,z) /\ LHS(x,y) -> RHS(x,y)
```

Notice that tactically, we want to prove (6a2) first and know 
what values t1 should have.
In other words, by solving (6a2), we know what the (existential quantified)
variables t1 should be, and then we use that values to solve (6b).
This is reflected by the fact in (6b), we also have `LHS(z,y)[t1/y1]` on the lhs. 
Also, we may first try (6a2)+(6b), before (6a1). 

We end this section by a summary.

```
Proof obligation is
(1) p(x) /\ LHS -> RHS

(One case of) the definition is
p(x) === ... \/ exists z . p(z) /\ BODY

Here's how to apply a KT.

First, unfold p(x) according to the definition (about one case).
In the meantime, obtain the substitution [z/x]

(1a) p(z) /\ BODY /\ LHS -> RHS

Calculate LHS' === LHS[z/x] and RHS' === RHS[z/x]

If RHS' has p:
  For every variable yi in FV(LHS,RHS) \ x,
    if yi occurs in a critical position in the p in RHS'
    rename it to a fresh variable ti

Denote the final substitution [t1/y1]. 

Calculate LHS'' === LHS'[t1/y1] and RHS'' === RHS[t2/t2]

Prove

EITHER BOTH
  (6a2) BODY /\ LHS -> LHS''
  (6b) LHS'' /\ RHS'' /\ BODY /\ LHS -> RHS
OR JUST
  (6a1) BODY /\ LHS -> RHS           // this is unlikely to prove

  
```

### Implementation of KT

```
GAtom,GConstraints -> HAtom,HConstraints  /* HAtom and GAtom contains the same recursive predicate */
body(CP, BAtom, BConstraints)    /* BAtom and GAtom contains the same recursive predicate */

Variables in GAtom are called active variables.
Variables in GConstraints,HAtom,HConstraints but not in GAtom are called passive variables.

ActiveVars = ...
PassiveVars = ...

// BODY is BConstraints
// LHS is GConstraints
// RHS is HAtom,HConstraints

The key here is that every critical variables in HAtom must be renamed.

We do that in two steps.

First, Subst1 is applied according to the unfold.
Some critical variables might be renamed (even renaming to themselves is OK ... ), 
while some are not.
Then we apply Subst2, and make sure all those remaining critical
variables are renamed to something fresh.

// Subst1 is [z/x]
get_unifier([GAtom],[BAtom],Subst1)
substitute(Subst1, GConstraints, GConstraints1)
substitute(Subst1, HAtom, HAtom1)
substitute(Subst1, HConstraints, HConstraints1)

// Subst2 is [t1/y1]
* collect all critical variables in HAtom, say, HAtomCriticalVars
* calculate the intersection of HAtomCriticalVars and PassiveVars, and denote the result HAtomPassiveCriticalVars
* construct the substitution Subst2 = [HAtomPassiveCriticalVars --> FreshCopyHAtomPassiveCriticalVars]
substitute(Subst2, GConstraints1, GConstraints2)
substitute(Subst2, HAtom1, HAtom2)
substitute(Subst2, HConstraints1, HConstraints2)

(6a2) BConstraints,GConstraints -> GConstraints2
(6b)  HAtom2,GConstraints2,HConstraints2,BConstraints,GConstraints -> HAtom,HConstraints
```

### `ll(H,X,Y,F) -> lr(H,X,Y,F)`

We start the proof in the middle.

```
(4) X>0 /\ X!=Y /\ T=H[X] /\ X notin F1 /\ F=F1+{X} /\ lr(H,T,Y,F1) -> lr(H,X,Y,F)

apply KT

Consider the nonbasic case.

/* variable vector x is H,T,Y,F1
 * variable vector y is X,F
 * p(x) is lr(H,T,Y,F1)
 * LHS is X>0 /\ X!=Y /\ T=H[X] /\ X notin F1 /\ F=F1+{X}
 * RHS is lr(H,X,Y,F)
 * p(z) is lr(H,T,T1,F2)
 * substitution [z/x] is [T1/Y,F2/F1]
 * BODY is T1>0 /\ T!=Y /\ Y=H[T1] /\ T1 notin F2 /\ F1=F2+{T1}
 * critical positions are 3,4, because lr(H,T,Y,F1) ---unfold---> lr(H,T,T1,F2)
 * noncritical positions are 1,2
 * LHS' === LHS[z/x] is X>0 /\ X!=T1 /\ T=H[X] /\ X notin F2 /\ F=F2+{X}
 * RHS' === RHS[z/x] is lr(H,X,T1,F)
 * RHS' has lr, and T1,F are in critical positions
 * variable vector y1 is F
 * variable vector t1 is F3, a fresh copy of y1
 * substitution [t1/y1] is [F3/F]
 * LHS'' === LHS'[t1/y1] is X>0 /\ X!=T1 /\ T=H[X] /\ X notin F2 /\ F3=F2+{X}
 * RHS'' === RHS'[t1/y1] is lr(H,X,T1,F3)
 */

prove BOTH
(4a2) T1>0 /\ T!=Y /\ Y=H[T1] /\ T1 notin F2 /\ F1=F2+{T1}   // BODY
      /\ X>0 /\ X!=Y /\ T=H[X] /\ X notin F1 /\ F=F1+{X}     // LHS
   -> X>0 /\ X!=T1 /\ T=H[X] /\ X notin F2 /\ F3=F2+{X}      // LHS''
(4b) X>0 /\ X!=T1 /\ T=H[X] /\ X notin F2 /\ F3=F2+{X}       // LHS''
     /\ lr(H,X,T1,F3)                                        // RHS''
     /\ T1>0 /\ T!=Y /\ Y=H[T1] /\ T1 notin F2 /\ F1=F2+{T1} // BODY
     /\ X>0 /\ X!=Y /\ T=H[X] /\ X notin F1 /\ F=F1+{X}      // LHS
  -> lr(H,X,Y,F)                                             // RHS

remove simple constraints from (4a2)
(4a2-1) T1>0 /\ T!=Y /\ Y=H[T1] /\ T1 notin F2 /\ F1=F2+{T1}   // BODY
        /\ X>0 /\ X!=Y /\ T=H[X] /\ X notin F1 /\ F=F1+{X}     // LHS
     -> /\ X!=T1 /\ X notin F2 /\ F3=F2+{X}

proved by (DP).

(Right Unfold) on (4b)
(4b-1) X>0 /\ X!=T1 /\ T=H[X] /\ X notin F2 /\ F3=F2+{X}       // LHS''
       /\ lr(H,X,T1,F3)                                        // RHS''
       /\ T1>0 /\ T!=Y /\ Y=H[T1] /\ T1 notin F2 /\ F1=F2+{T1} // BODY
       /\ X>0 /\ X!=Y /\ T=H[X] /\ X notin F1 /\ F=F1+{X}      // LHS
    -> lr(H,X,T2,F4) /\ T2>0 /\ X!=Y /\ Y=H[T2] /\ T2 notin F4 /\ F=F4+{T2}
    
prove by (DP).

QED.

To see why (4b-1) can be proved by (DP), notice that    
if we let T2 = T1 and F4 = F3 and remove simple constraints, we get
(4b-1) X>0 /\ X!=T1 /\ T=H[X] /\ X notin F2 /\ F3=F2+{X}       // LHS''
       /\ lr(H,X,T1,F3)                                        // RHS''
       /\ T>0 /\ T!=Y /\ Y=H[T1] /\ T1 notin F2 /\ F1=F2+{T1}  // BODY
       /\ X>0 /\ X!=Y /\ T=H[X] /\ X notin F1 /\ F=F1+{X}      // LHS
    -> T1 notin F3 /\ F=F3+{T1}

T1 notin F3, because T1 notin F2, and F3=F2+{X}, and X!=T1
F=F3+{T1}, because F=F1+{X}=F2+{T1}+{X}=F3+{T1}.
```

# Examples from Separation Logic

## `ll(H,X,Y,F) -> lr(H,X,Y,F)`

We proved it in the previous section.

## `lr(H,X,Y,F) -> ll(H,X,Y,F)`

TODO.

## `ll(H,X,Y,F) /\ list(H,Y,G) /\ disjoint(F,G) /\ K=F+G -> list(H,X,K)`

```
Defintions.

ll(H,X,Y,F) ===
  (case A) X=Y /\ F=emptyset
  (case B) ll(H,X1,Y,F1) /\ X>0 /\ X!=Y /\ X1=H[X] /\ X notin F /\ F=F1+{X}

list(H,X,F) ===
  (case A) X=0 /\ F=emptyset
  (case B) list(H,X1,F1) /\ X>0 /\ X1=H[X] /\ X notin F /\ F=F1+{X}
  
(1) ll(H,X,Y,F) /\ list(H,Y,G) /\ disjoint(F,G) /\ K=F+G -> list(H,X,K)

apply KT.

Two cases.

TODO

```

### `mul4(X) -> even(X)` (DO NOT READ)

_Definitions._

```
unfold(mul4(X),
  [
  body([], [eq(X, 0)]),
  body([mul4(Y)],
       [gt(X, 0), eq(X, plus(Y, 4))])
  ]).

unfold(even(X),
  [
  body([], [eq(X, 0)]),
  body([even(Y)],
       [gt(X, 0), eq(X, plus(Y, 2))])
  ]).
```

_Proof._

```

(1) mul4(X) -> even(X)

apply (KT) on (1) /* no need for (Plugin) and (Plugout) for this example */

proof rule (KT) is
  goto the definition of mult4
  for every body B in the definition of mult4:
    let B' = substitute mult4(Y) for even(Y) in B
    generate a new obligation B' -> even(X)

(2-1) X=0 -> even(X)
(2-2) even(Y) /\ X>0 /\ X=Y+4 -> even(X)

apply (RU) on (2-1). done.

apply (RU) on (2-2).

(3) even(Y) /\ X>0 /\ X=Y+4 -> even(Y') /\ X>0 /\ X=Y'+2

apply (RU) on (3).

(4) even(Y) /\ X>0 /\ X=Y+4 -> even(Y'') /\ Y'>0 /\ Y''=Y'+2 /\ X>0 /\ X=Y'+2

apply (DP) on (4).
```

# A bit(e) of theory

## Least fixpoints

Least fixpoints (lfp) are defined using the `mu` construct.
Given `x` and `e` where `x` doesn't occur negatively,
`mu x . e` denotes the lfp of `e` wrt `x`.
This means the follows.

In terms of provability, we define two axioms for `mu x . e`:
```
(Fix) mu x . e = e[(mu x . e)/x]
      e[e'/x] -> e'
(KT)  --------------
      mu x . e -> e'
```

Semantically, 
given a model with carrier set `M` and
its powerset `P(M)`,
the pattern `e` (wrt `x`) can be regarded as a 
function `Fe : P(M) -> P(M)`, defined as follows:
```
Fe(X) = \barrho[X/x](e)
```
where `\barrho[X/x](e)` means the interpretation of `e` in the
valuation `rho` where `rho(x) = X`.
This is, obviously, against the matching logic semantics,
because one cannot assign a subset to a variable.
But let's not worry about that for now and assume we can do it.

Then since `x` has no negative occurrence, 
the function `Fe : P(M) -> P(M)` is monotonic (wrt set containment
relation).
By the famous Knaster-Tarski theorem, `Fe` admits a unique lfp,
denoted as `mu Fe`, which we define as the _intended interpretation_
of the pattern `mu x . e`.
In other words, `\barrho(mu x . e) = mu Fe`.

One can easily check that the two axioms `(Fix)` and `(KT)` are sound
wrt the intended interpretation of lfp.

There remains a difficult fundenmental question:
how does one define the construct `mu` so that it admits the above
intended interpretation as one possible interpretation?
Notice that the "easy" guess `mu x . e === exists x . mu0(x, e)`,
doesn't work.
Hint: 
prove that if `Gamma |- e1 -> e2` for some `Gamma`,
then `Gamma |- mu x . e1 -> mu x . e2`,
which is unsound in the intended interpretation.
More hints: consider `mu x . x` and `mu x . (x /\ c)` where
`c` is any constant functional symbol.

We do not intend to answer this fundenmental question in the PLDI paper.
In fact, we focus on _axioms and proofs_, leaving _semantics and models_ aside,
just for now.

### Least fixpoints: from sets to relations

`mu x . e` defines a subset.
Very powerful.
It already powers us to define
linear temporal logic (LTL),
computation tree logic (CTL),
dynamic logic (DL),
and reachabiliity logic (RL),
_faithfully_ in matching logic.

But one may ask: how do I define a _recursive symbol_
`r(x,y)` using `mu`?
As an example, the `ll(x,y)` matches all heaplets that are
linked lists from `x` to `y`, which is often defined
recursively:
```
ll(x,y) =lfp (emp /\ x=y) \/ exists t . (x|->t * ll(t,y) /\ x!=y /\ x!=0)
```
The question is, can we define `ll(x,y)` using `mu`?
The answer is positive;
but we need to first introduce lambda calculus.

## Lambda calculus

Lambda calculus `lambda x . e` can be defined in matching logic.
There are also deep fundenmental questions about the semantics
and models of the definition, but that's not the focus of this work.
To subsume lambda calculus and prove all that lambda calculus can prove,
we need only two axioms
```
(alpha) lambda x . e = lambda y . e[y/x]
(beta)  app((lambda x . e), e') = e[e'/x]
```

## `mu` meets `lambda`

`mu` and `lambda` give us full power of induction and recursion.
Back to `ll`, we can now define it as
```
ll = mu f lambda x lambda y . (emp /\ x=y) \/ exists t . (x|->t * app(app(f,t),y) /\ x!=y /\ x!=0)
```
Notice `ll` is a _constant symbol_ taking no argument,
and `ll(x,y)` is written as `app(app(ll,x),y)`.
To easy our notation, we abbreviate `app(app(ll,x),y)` as `ll@(x,y)`.

## Least fixpoints in a context: (Plugin) and (Plugout)

Let's look at the following example.
Define `ll` and `lr` be two lfp:
```
ll = mu f lambda x lambda y . (emp /\ x=y) \/ exists t . (x|->t * f@(t,y) /\ x!=y /\ x!=0)
lr = mu f lambda x lambda y . (emp /\ x=y) \/ exists t . (f@(x,t) * t|->y /\ x!=y /\ x!=0)
```
How can we prove `ll@(x,y) -> lr@(x,y)`?
To be clear, how to prove `app(app(ll,x),y) -> app(app(lr,x),y)`?

Notice that (KT) is not applicable here, as `ll` occurs in a context.
One attempt is to apply (Framing) rules twice and prove `ll -> lr`,
but I failed on that approach.

Here I'm introducing a _general and systematic_ approach to deal with
the above situation, i.e., lfp occurs on the lhs within some context `C`.

Assume we have an implication `C[phi] -> psi`. 
If `C` is an _extensional_ context, which means
```
|- C[bottom] -> bottom
|- C[phi1 \/ phi2] -> C[phi1] \/ C[phi2]
|- C[exists x . phi] -> exists x . C[phi]
```
then one can prove that
```
|- C[phi] -> psi if and only if |- phi -> exists x . x /\ floor(C[x] -> psi)
```

Let `C'[HOLE] === exists x . x /\ floor(C[x] -> HOLE)`, called the _implication context_
of `C`, then `|- C[phi] -> psi` if and only if `|- phi -> C'[psi]`.
In particular, `|- C[C'[psi]] -> psi`.
Using this new notation of implication context, we have
```
                 ----(Plugout)--->
|- C[phi] -> psi   if and only if  |- phi -> C'[psi]          /* if C is extensional */
                 <---(Plugin)-----

As a special case,

|- C[C'[psi]]    ----(Collapse)--> |- psi                     /* if C is extensional */

|- D[C[C'[psi]]] ----(Collapse)--> |- D[psi]                  /* if C and D are extensional */
```

## The full example: `ll@(x,y) -> lr@(x,y)`

We work out the example `ll@(x,y) -> lr@(x,y)` and present
the entire proof here.
The purpose is two-fold: 
(1) to demonstrate (Plugin) and (Plugout);
and (2) to eluminate good proving strategy.

Again, we emphasize that proving `ll -> lr` **will not work**.
(Or, let me know if you prove me wrong).

Proof.

```
Fixpoint definitions.
ll = mu f lambda x y . (emp /\ x=y) \/ exists t . (x|->t * f@(t,y) /\ x!=y /\ x!=0)
lr = mu f lambda x y . (emp /\ x=y) \/ exists t . (f@(x,t) * t|->y /\ x!=y /\ x!=0)

Proof obligation.
(G) ll@(x,y) -> lr@(x,y)

Proof.

apply (Plugout) on (G). /* !!!HOT SPOT!!! */

(G-1) ll -> exists f . (f /\ floor(f@(x,y) -> lr@(x,y)))

let F === exists f . (f /\ floor(f@(x,y) -> lr@(x,y))) in (G-1).

(G-2) ll -> F

apply (Forall) on (G-2). /* |- A -> forall x . B implies |- A -> B */

(G-3) ll -> forall x y . F

apply (KT) on (G-3).

(G-4) lambda x y . (emp /\ x=y) \/ exists t . (x|->t * (forall x y . F)@(t,y) /\ x!=y /\ x!=0)
   -> forall x y . F

apply (UG) on (G-5). /* universal generalization */

(G-5) lambda x y . (emp /\ x=y) \/ exists t . (x|->t * (forall x y . F)@(t,y) /\ x!=y /\ x!=0)
   -> F

apply (Plugin) on (G-5). /* !!!HOT SPOT!!! you may want to go back to (G-1) and check what F is */

(G-6) (emp /\ x=y) \/ exists t . (x|->t * (forall x y . F)@(t,y) /\ x!=y /\ x!=0) 
   -> lr@(x,y)

apply (SplitLeft) on (G-6).

(G-6-1) emp /\ x=y -> lr@(x,y) /* whose proof we omit (for now) */

(G-6-2) exists t . (x|->t * (forall x y . F)@(t,y) /\ x!=y /\ x!=0) -> lr@(x,y)

apply (Exists) on (G-6-2). /* |- A(t) -> B implies |- (exists t . A(t)) -> B if t not in FV(B) */

(G-6-3) x|->t * (forall x y . F)@(t,y) /\ x!=y /\ x!=0 -> lr@(x,y)

apply (Inst, (forall x y . F), x=t, y=y) on (G-6-3).

(G-6-4) x|->t * (F[t/x][y/y])@(t,y) /\ x!=y /\ x!=0 -> lr@(x,y)

expand F[t/x][y/y] in (G-6-4).

(G-6-5) x|->t * (exists f . f /\ floor(f@(t,y) -> lr@(t,y)))@(t,y) /\ x!=y /\ x!=0 -> lr@(x,y)

apply (Collapse) on (G-6-5). /* !!!HOT SPOT!!! */

(G-6-6) x|->t * lr@(t,y) /\ x!=y /\ x!=0 -> lr@(x,y)

apply (Plugout) on (G-6-6).

(G-6-7) lr -> exists f . (f /\ floor(x|->t * f@(t,y) /\ x!=y /\ x!=0 -> lr@(x,y)))

let G = exists f . (f /\ floor(x|->t * f@(t,y) /\ x!=y /\ x!=0 -> lr@(x,y))) in (G-6-7).

(G-6-8) lr -> G

apply (Forall) on (G-6-8).

(G-6-9) lr -> forall x y t . G

apply (KT) on (G-6-10).

(G-6-10) lambda x y . (emp /\ x=y) \/ exists t' . ((forall x y t . G)@(x,t') * t'|->y /\ x!=y /\ x!=0)
      -> forall x y t . G

apply (UG) on (G-6-10).

(G-6-11) lambda x y . (emp /\ x=y) \/ exists t' . ((forall x y t . G)@(x,t') * t'|->y /\ x!=y /\ x!=0)
      -> G

apply (Plugin) on (G-6-11).

(G-6-12) x|->t * (emp /\ t=y \/ exists t' . ((forall x y t . G)@(t,t') * t'|-> y /\ t!=y /\ t!=0)) /\ x!=y /\ x!=0 
      -> lr@(x,y)

apply (Propataion) on (G-6-12).

(G-6-13) x|->t * emp /\ t=y /\ x!=y /\ x!=0
      \/ x|->t * exists t' . ((forall x y t . G)@(t,t') * t'|-> y /\ t!=y /\ t!=0) /\ x!=y /\ x!=0
      -> lr@(x,y)

apply (SplitLeft) on (G-6-13).

(G-6-13-1) x|->t * emp /\ t=y /\ x!=y /\ x!=0 -> lr@(x,y) /* whose proof we omit (for now) */

(G-6-13-2) x|->t * exists t' . ((forall x y t . G)@(t,t') * t'|-> y /\ t!=y /\ t!=0) /\ x!=y /\ x!=0
        -> lr@(x,y)

apply (Exists) on (G-6-13-2).

(G-6-13-3) x|->t * ((forall x y t . G)@(t,t') * t'|-> y /\ t!=y /\ t!=0) /\ x!=y /\ x!=0
        -> lr@(x,y)

apply (RightUnfold,case=2) on (G-6-13-3).

(G-6-13-4) x|->t * ((forall x y t . G)@(t,t') * t'|-> y /\ t!=y /\ t!=0) /\ x!=y /\ x!=0
        -> exists t'' . lr@(x,t'') * t''|->y /\ x!=y /\ x!=0

apply (Inst, t''=t') on (G-6-13-4).

(G-6-13-5) x|->t * ((forall x y t . G)@(t,t') * t'|-> y /\ t!=y /\ t!=0) /\ x!=y /\ x!=0
        -> lr@(x,t') * t'|->y /\ x!=y /\ x!=0

apply (Inst, (forall x y t . G), x=x,y=t',t=t) on (G-6-13-5).

(G-6-13-6) x|->t * ((G[x/x][t'/y][t/t])@(t,t') * t'|-> y /\ t!=y /\ t!=0) /\ x!=y /\ x!=0
        -> lr@(x,t') * t'|->y /\ x!=y /\ x!=0

expand G[x/x][t'/y][t/t] on (G-6-13-6).

(G-6-13-7) x|->t * ((exists f . (f /\ floor(x|->t * f@(t,t') /\ x!=t' /\ x!=0 -> lr@(x,t'))))@(t,t') * t'|-> y /\ t!=y /\ t!=0) /\ x!=y /\ x!=0
        -> lr@(x,t') * t'|->y /\ x!=y /\ x!=0

apply (CaseAnalysis, x=t') on (G-6-13-7). /* this may look like magic. why case analysis here? see later. */

(G-6-13-7-1) x|->t * ((exists f . (f /\ floor(x|->t * f@(t,t') /\ x!=t' /\ x!=0 -> lr@(x,t'))))@(t,t') * t'|-> y /\ t!=y /\ t!=0) /\ x!=y /\ x!=0
          /\ x=t'
          -> lr@(x,t') * t'|->y /\ x!=y /\ x!=0 /* notice that lhs is unsat: x|->t * ... * t'|->y /\ x=t' /\ t!=y /\ ... */

(G-6-13-7-2) x|->t * ((exists f . (f /\ floor(x|->t * f@(t,t') /\ x!=t' /\ x!=0 -> lr@(x,t'))))@(t,t') * t'|-> y /\ t!=y /\ t!=0) /\ x!=y /\ x!=0
          /\ x!=t'
          -> lr@(x,t') * t'|->y /\ x!=y /\ x!=0

apply (LeftUnsat) on (G-6-13-7-1).

done

apply (Collapse) on (G-6-13-7-2). /* thanks to CaseAnalysis, we have x!=t' in the context, so Collaspe can be applied */

(G-6-13-7-2) lr@(x,t') * t'|->y /\ t!=y /\ t!=0 /\ x!=y /\ x!=0
          -> lr@(x,t') * t'|->y /\ x!=y /\ x!=0

apply (DirectProof) on (G-6-13-7-2).

done

qed.
```

# More examples

## (LTL Ind) `[] (P -> o P) /\ P -> [] P`

This is the famous induction proof rule in LTL.
It is valid and can be proved with (KT) in matching logic.
To do that, we need to define LTL in matching logic.

It is known how to define LTL in matching logic.
Here shows the definition.
We let `*` be a unary matching logic symbol, called "strong next".
Let `o P = not * not P` called "weak next".
Let `[] P` be a greatest fixpoint defined as
```
[] P =gfp P /\ o [] P
```
We need two axioms to capture LTL.
They are
```
(Lin) * P -> o P for any pattern P
(Inf) * top
```

The following axiom schema is provable from the above two axioms.
```
(Propagation o) o(P /\ Q) = o P /\ o Q
```

_Proof tree_

```
(G) [] (P -> o P) /\ P -> [] P

apply (KT) on (G).  /* we don't need (Plugin) and (Plugout) */

(G-1) [] (P -> o P) /\ P -> [] (P -> o P) /\ P /\ o ([] (P -> o P) /\ P)

apply (Split) on (G-1).

(G-2-1) [] (P -> o P) /\ P -> [] (P -> o P)
(G-2-2) [] (P -> o P) /\ P -> P
(G-2-3) [] (P -> o P) /\ P -> o ([] (P -> o P) /\ P)

apply (DP) on (G-2-1). 

done

apply (DP) on (G-2-2).

done

apply (Propagation o) on (G-2-3).

(G-2-4) [] (P -> o P) /\ P -> o [] (P -> o P) /\ o P

apply (Split) on (G-2-4)

(G-2-5-1) [] (P -> o P) /\ P -> o [] (P -> o P)
(G-2-5-2) [] (P -> o P) /\ P -> o P

apply (Fix) on (G-2-5-1)

(G-2-5-1-1) (P -> o P) /\ o [] (P -> o P) /\ P -> o [] (P -> o P)

apply (DP) on (G-2-5-1-1).

done

apply (Fix) on (G-2-5-2).

(G-2-5-2-1) (P -> o P) /\ o [] (P -> o P) /\ P -> o P

apply (DP) on (G-2-5-2-1).

done
```

## CTL and its proof rules.

The key CTL operators are defined in matching logic as:
```
AX P === o P // strong next
EX P === * P // weak next
P AU Q === mu f . (Q \/ (P /\ o f)) // all-path until
P EU Q === mu f . (Q \/ (P /\ * f)) // one-path until
EF P === mu f . P \/ * f // one-path eventually
AG P === nu f . P /\ o f // all-path always
AF P === mu f . P \/ o f // all-path eventually
EG P === nu f . P \/ * f // one-path always
```

CTL assumes infinite traces, and thus requires the following domain specific axiom
```
(Inf) * top
```

We **may** need a few domain specific axioms to help the prover.
For example,
```
(DualWNext) ! * ! P = o P
(DualSNext) ! o ! P = * P
(Next) o P /\ * Q -> *(P /\ Q)
```

We **may** need two duality rules for fixpoints.
```
(NegLFP) ! (mu f . P) = nu f . ! P [!f / f]
(NegGFP) ! (nu f . P) = mu f . ! P [!f / f]
```

We **may** need a few propositional rules (i.e., (DP)), to canonicalize the patterns. 
```
(DeMorgen) !(P \/ Q) = !P /\ !Q
(DeMorgen) !(P /\ Q) = !P \/ !Q

      Q -> R           /* more generally it should be (P -> Q) /\ P /\ Q -> R
(MP) ------------------------
     (P -> Q) /\ P -> R

           P /\ Q -> R
(NegCase) --------------
           P -> (!Q \/ R)
```

The above rules will help make the proof _human readable_.
But maybe they are not really necessary. 
I used them in my proof, though.

### (CTL6) `AG(R -> (!Q /\ * R)) /\ R -> !(P AU Q)`

_Proof._

```
(G) AG(R -> (!Q /\ * R)) /\ R -> !(P AU Q)

by definition of P AU Q, this is the same as

(G) AG(R -> (!Q /\ * R)) /\ R -> !(mu f . (Q \/ (P /\ o f)))

apply (NegLFP) on (G).

(G-1) AG(R -> (!Q /\ * R)) /\ R -> nu f . !(Q \/ (P /\ o ! f))

apply (DeMongen) on (G-1).

(G-2) AG(R -> (!Q /\ * R)) /\ R -> nu f . (!Q /\ (!P \/ ! o ! f))

apply (DualWNext) on (G-2).

(G-3) AG(R -> (!Q /\ * R)) /\ R -> nu f . (!Q /\ (!P \/ * f))

apply (KT) on (G-3).

(G-4) AG(R -> (!Q /\ * R)) /\ R
   -> !Q /\ (!P \/ * (AG(R -> (!Q /\ * R)) /\ R)))
   
apply (Split) on (G-4).

(G-4-1) AG(R -> (!Q /\ * R)) /\ R -> !Q
(G-4-2) AG(R -> (!Q /\ * R)) /\ R -> (!P \/ * (AG(R -> (!Q /\ * R)) /\ R)))

apply (Fix) on (G-4-1).

(G-4-1-1) (R -> (!Q /\ *R)) /\ (o AG(R -> (!Q /\ * R))) /\ R -> !Q

apply (DP) on (G-4-1-1).

done

apply (Fix) on (G-4-2).

(G-4-2-1) (R -> (!Q /\ *R)) /\ (o AG(R -> (!Q /\ * R))) /\ R -> (!P \/ * (AG(R -> (!Q /\ * R)) /\ R)))

apply (MP) on (G-4-2-1).

(G-4-2-2) !Q /\ *R /\ (o AG(R -> (!Q /\ * R))) -> (!P \/ * (AG(R -> (!Q /\ * R)) /\ R)))

apply (Next) on (G-4-2-2).

(G-4-2-3) * (R /\ AG(R -> (!Q /\ * R))) -> (!P \/ * (AG(R -> (!Q /\ * R)) /\ R)))

apply (DP) on (G-4-2-3).

done
```

### (CTL7) `AG(R -> (!Q /\ (P -> o R))) /\ R -> !(P EU Q)`

_Proof_.

```
(G) AG(R -> (!Q /\ (P -> o R))) /\ R -> !(P EU Q)

(G) AG(R -> (!Q /\ (P -> o R))) /\ R -> !(mu f . (Q \/ (P /\ * f)))

apply (NegLFP) on (G).

(G-1) AG(R -> (!Q /\ (P -> o R))) /\ R
   -> nu f . !(Q \/ (P /\ * ! f))
   
apply (DeMongen) on (G-1).

(G-2) AG(R -> (!Q /\ (P -> o R))) /\ R
   -> nu f . (!Q /\ (!P \/ ! * ! f)))
   
apply (NegSNext) on (G-2).

(G-3) AG(R -> (!Q /\ (P -> o R))) /\ R
   -> nu f . (!Q /\ (!P \/ o f)))
   
apply (KT) on (G-1).

(G-2) AG(R -> (!Q /\ (P -> o R))) /\ R
   -> !Q /\ (!P \/ o(AG(R -> (!Q /\ (P -> o R))) /\ R))

apply (Split) on (G-2).

(G-2-1) AG(R -> (!Q /\ (P -> o R))) /\ R -> !Q
(G-2-2) AG(R -> (!Q /\ (P -> o R))) /\ R -> (!P \/ o(AG(R -> (!Q /\ (P -> o R))) /\ R))

apply (Fix) on (G-2-1).

(G-2-1-1) (R -> (!Q /\ (P -> o R))) /\ (o AG(R -> (!Q /\ (P -> o R)))) /\ R -> !Q

apply (DP) on (G-2-1-1).

done

apply (Fix) on (G-2-2).

(G-2-2-1) (R -> (!Q /\ (P -> o R))) /\ (o AG(R -> (!Q /\ (P -> o R)))) /\ R
       -> (!P \/ o(AG(R -> (!Q /\ (P -> o R))) /\ R))
       
apply (MP) on (G-2-2-1).

(G-2-2-2) !Q /\ (P -> o R) /\ (o AG(R -> (!Q /\ (P -> o R))))
       -> (!P \/ o(AG(R -> (!Q /\ (P -> o R))) /\ R))

apply (NegCase) on (G-2-2-2).
(G-2-2-3) !Q /\ (P -> o R) /\ (o AG(R -> (!Q /\ (P -> o R)))) /\ P
       -> o(AG(R -> (!Q /\ (P -> o R))) /\ R)

apply (MP) on (G-2-2-3).

(G-2-2-4) !Q /\ o R /\ (o AG(R -> (!Q /\ (P -> o R))))
       -> o(AG(R -> (!Q /\ (P -> o R))) /\ R)
       
apply (Propagation o) on (G-2-2-4).

(G-2-2-5) !Q /\ o R /\ (o AG(R -> (!Q /\ (P -> o R))))
       -> o(AG(R -> (!Q /\ (P -> o R)))) /\ o R
       
apply (DP).

done
```

## SL `ll@(x,y) * list@(y) -> list@(x)`

_Definitions._

```
ll = mu f . lambda x y . (emp /\ x=y) \/ exists t . (x|->t * f@(t,y) /\ x!=y /\ x!=0)
list = mu f . lambda x . (emp /\ x=0) \/ exists t . (x|->t * f@(t) /\ x!=0)
```

_Propagation rules._

```
(P \/ Q) * H = P * H \/ Q * H, where * is the merge
```

_Proof._
```
(G) ll@(x,y) * list@(y) -> list@(x)

apply (Plugout) on (G).

(G-1) ll -> exists h . h /\ floor(h@(x,y) * list@(y) -> list@(x))

let F === exists h . h /\ floor(h@(x,y) * list@(y) -> list@(x))

apply (Forall) on (G-1).

(G-2) ll -> forall x y . F

apply (KT) on (G-1).

(G-2) lambda x y . (emp /\ x=y) \/ exists t . (x|->t * (forall x y . F)@(t,y) /\ x!=y /\ x!=0)
   -> forall x y . exists h . h /\ floor(h@(x,y) * list@(y) -> list@(x))
   
apply (UG) on (G-2).

(G-3) lambda x y . (emp /\ x=y) \/ exists t . (x|->t * (forall x y . F)@(t,y) /\ x!=y /\ x!=0)
   -> exists h . h /\ floor(h@(x,y) * list@(y) -> list@(x))

apply (Plugin) on (G-3).

(G-4) ((emp /\ x=y) \/ exists t . (x|->t * (forall x y . F)@(t,y) /\ x!=y /\ x!=0)) * list@(y) -> list@(x)

apply (Propagation) on (G-4).

(G-5) ((emp /\ x=y) * list@(y)) \/ (exists t . (x|->t * (forall x y . F)@(t,y) /\ x!=y /\ x!=0)) * list@(y) -> list@(x)

apply (Split) on (G-5).

(G-5-1) list@(y) /\ x=y -> list@(x)
(G-5-2) (exists t . (x|->t * (forall x y . F)@(t,y) /\ x!=y /\ x!=0)) * list@(y) -> list@(x)

apply (DP) on (G-5-1).

done

apply (Exists) on (G-5-2).

(G-5-3) x|->t * (forall x y . F)@(t,y) * list@(y) /\ x!=y /\ x!=0  -> list@(x)

apply (Inst, forall x y . F, x=t, y=y) on (G-5-3).

(G-5-4) x|->t * (F[t/x][y/y])@(t,y) * list@(y) /\ x!=y /\ x!=0  -> list@(x)

expand F.

(G-5-4) x|->t * (exists h . h /\ floor(h@(t,y) * list@(y) -> list@(t)))@(t,y) * list@(y) /\ x!=y /\ x!=0  -> list@(x)

apply (Collapse) on (G-5-4).

(G-5-5) x|->t * list@(t) /\ x!=y /\ x!=0 -> list@(x)

apply (Fix) on (G-5-5). 

...
```

## Some coinduction examples

_TODO._

## Some program verification examples

_TODO._

# Proof rules

## The fragment, the syntax

The following syntax is chosen so that a very wide range of
interesting problems, including `ll@(x,y) -> lr@(x,y)` and
`[] (P -> o P) /\ P -> [] P`, can be encoded using the syntax.

**Please see `fix.maude` for all definitions.**

```
Variable ::= x | y | z | ...
Pattern  ::= Variable
           | Pattern "/\" Pattern
           | Pattern "\/" Pattern
           | Pattern "->" Pattern
           | "not" Pattern
           | forall VariableList "." Pattern
           | exists VariableList "." Pattern
           | lambda VariableList "." Pattern     /* lambda abstraction */
           | Pattern "@" "(" PatternList ")"     /* function application */
           | mu Variable "." Pattern             /* lfp */
           | nu Variable "." Pattern             /* gfp */
           | floor "(" Pattern ")"               /* totality */
           /* extendable user-defined domain specific syntax (known as the shallow embedding) */
           /* for infinite-trace LTL */
           | "o" Pattern         /* next */
           | "[]" Pattern        /* always */
           | "<>" Pattern        /* eventually */
           | Pattern "U" Pattern /* until */
           /* for separation logic */
           | "emp"
           | Pattern "|->" Pattern
           | Pattern "*" Pattern
           | "ll"
           | "lr"
```

## Proof rules

```
/* Basic Propositional reasoning */

P -> P1  P -> P2  ...  P -> Pn
------------------------------- (/\-IntroR)
P -> P1 /\ P2 /\ ... /\ Pn

P -> Pi
-------------------------------- (\/-IntroR)
P -> P1 \/ P2 \/ ... \/ Pn

P1 -> P ... Pn -> P
-------------------------------- (\/-IntroL)
P1 \/ ... \/ Pn -> P


Pi -> P
-------------------------------- (/\-IntroL)
P1 /\ ... /\ Pn -> P

/* Basic FOL reasoning */

P -> Q                 if x not in FV(P)
---------------------- (UG) // universal generalization
P -> forall x . Q

P -> Q[t/x]            if x not in FV(P) and t is a term
---------------------- (exists-IntroR) // t is often obtained from unifying P and Q
P -> exists x . Q

forall x . P /\ P[t/x] -> Q   if t is a term
----------------------------  (forall-InstL) // instantiate forall x . P
forall x . P -> Q

/* Equations */

An equation lhs = rhs means that one can substitute lhs
for rhs in any context. 

(Fix-LFP) mu x . e = e[mu x . e / x]  // least fixpoint

(Fix-GFP) nu x . e = e[nu x . e / x]  // greatest fixpoint

e[e'/x] -> e'
--------------- (KT-LFP)
mu x . e -> e'

e' -> e[e'/x]
--------------- (KT-GFP)
e' -> nu x . e

P -> C'[Q]   where C'[Q] === exists x . x /\ floor(C[x] -> Q)
-------------(PlugoutL)
C[P] -> Q

C[P] -> Q    where C'[Q] === exists x . x /\ floor(C[x] -> Q)
-------------(PluginL)
P -> C'[Q]

C[C'[P]] -> Q where C'[Q] === exists x . x /\ floor(C[x] -> Q)
------------- (CollapseL)
P -> Q

C'[P] -> Q   where C'[P] === exists x . x /\ floor(P -> C[x])
-------------(PlugoutR)
P -> C[Q]

P -> C[Q]    where C'[P] === exists x . x /\ floor(P -> C[x])
-------------(PluginR)
C'[P] -> Q

P -> C[C'[Q]] where C'[P] === exists x . x /\ floor(P -> C[x])
------------- (CollapseR)
P -> Q

```


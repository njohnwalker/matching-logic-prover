KMaude

```maude
load ml.maude

fmod KMAUDE is
    extending META-MODULE * (  op _+_  : ModuleExpression ModuleExpression -> ModuleExpression
                            to op _++_ : ModuleExpression ModuleExpression -> ModuleExpression
                            ) .

    sorts KTerminal KNonTerminal KProduction .
    subsort String < KTerminal .
    subsort Sort < KNonTerminal .
    subsorts KTerminal KNonTerminal < KProduction .

    sort KAttributes .
    subsort AttrSet < KAttributes .

    sorts KSyntax KRule KSentence KSentences .
    subsorts KSyntax KRule < KSentence < KSentences .

    sort Modules .
    subsort Module < Modules .

    var ME : ModuleExpression . var H : Header . var IL : ImportList .
    vars S S' : Sort . var SS : SortSet . var SDS : SubsortDeclSet .
    var ODS : OpDeclSet . var MAS : MembAxSet .
    var ES : EquationSet . var RS : RuleSet .
    var KT : KTerminal . var KNT : KNonTerminal . vars KP KP' : KProduction .
    var KA : KAttributes . var KS : KSentences .

    op __ : KProduction KProduction -> KProduction [ctor assoc id: nil prec 25] .
    -----------------------------------------------------------------------------

    op _[_] : KSyntax KAttributes -> KSentence [right id: none prec 60] .
    op _[_] : KRule KAttributes -> KSentence [right id: none prec 60] .
    -------------------------------------------------------------------

    op syntax_     : Sort             -> KSyntax [prec 30] .
    op syntax_::=_ : Sort KProduction -> KSyntax [prec 30] .
    op rule_       : KTerm            -> KRule   [prec 30] .
    --------------------------------------------------------

    op .KSentences : -> KSentences .
    op __ : KSentences KSentences -> KSentences [ctor assoc comm id: .KSentences prec 80 format(d ni d)] .
    ------------------------------------------------------------------------------------------------------

    op imports_ : ModuleExpression -> Import .
    ------------------------------------------
    eq imports ME = including ME . .

    op kmod_is_sorts_.______endkm
            : Header ImportList SortSet SubsortDeclSet OpDeclSet MembAxSet EquationSet RuleSet KSentences -> SModule
            [ctor gather (& & & & & & & & &) format (d d s n++i ni d d ni ni ni ni ni ni n--i d)] .
    op module___endmodule
            : Header ImportList KSentences -> SModule
            [gather (& & &) format (d d n++i ni n--i d)] .
    op .Modules : -> Modules [ctor] .
    op __ : Modules Modules -> Modules [ctor assoc comm id: .Modules prec 98 format(d nn d)] .
    ------------------------------------------------------------------------------------------

    op opQid : KProduction -> Qid .
    -------------------------------
    eq opQid( KT     ) = qid(KT) .
    eq opQid( KNT    ) = '_ .
    eq opQid( KP KP' ) = qid(string(opQid( KP )) + string(opQid( KP' ))) .

    op args  : KProduction -> TypeList .
    ------------------------------------
    eq args( KT     ) = nil .
    eq args( KNT    ) = KNT .
    eq args( KP KP' ) = args(KP) args(KP') .

    eq module H IL KS endmodule = kmod H is IL sorts none . none none none none none KS endkm .

    eq kmod H is IL sorts SS . SDS ODS MAS ES RS .KSentences endkm
     = mod  H is IL sorts SS . SDS ODS MAS ES RS             endm  .

    eq kmod H is IL sorts SS     . SDS ODS MAS ES RS syntax S [none] KS endkm
     = kmod H is IL sorts SS ; S . SDS ODS MAS ES RS                 KS endkm .

    eq kmod H is IL sorts SS     . SDS                  ODS MAS ES RS syntax S ::= S' [none] KS endkm
     = kmod H is IL sorts SS ; S . SDS subsort S' < S . ODS MAS ES RS                        KS endkm .

    eq kmod H is IL sorts SS     . SDS ODS                                     MAS ES RS syntax S ::= KP [KA] KS endkm
     = kmod H is IL sorts SS ; S . SDS ODS op opQid(KP) : args(KP) -> S [KA] . MAS ES RS                      KS endkm [owise] .
endfm


reduce

module 'Test
    nil
    syntax 'Int
    syntax 'Int ::= 'Nat [none]
    syntax 'Int ::= 'Nat "hello" 'Nat
endmodule

module 'Test2
    imports 'Test
    syntax 'Rat
    syntax 'Rat ::= 'Int
    syntax 'Rat ::= 'Rat "+" 'Rat
    syntax 'Rat ::= 'Rat "/" 'Rat [ctor assoc comm]
endmodule

.


q


```
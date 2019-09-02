#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
sys.path.append('./moduls')
sys.path.append('./xmlrpc/moduls')

"""
  Hilfsklasse für das Parsen einer "freien" MWE-Abfrage.
"""
class WpSeTree:

  class DepNode:
    mapCat={}
    vChild=[]
    bAktive=True


  class CollapsRule:
    strHeadCat=""
    strDepCat=""
    strRelation=""
    strDirection=""

  """
    Anhand einer Liste von Lemmaformen wird eine geordnete Liste von Dependenzrelationen generiert anhand derer 
    ein MWE-Wortprofil berechnet werden kann
  """
  def lemma_and_pos_list_to_tree( self, listLemma, mapRelToId, mapRelIdToType ):

    if len(listLemma)==0:
      return []

    ### nur die Beste Kategorie betrachten
    for i in range(0,len(listLemma)):
      listLemma[i]=listLemma[i][0:1]

    vDepNode=[]
    for i in listLemma:
      mapping=i

      mapCat={}
      for j in mapping:
        mapCat[j['POS']]=j

      ### Terminal-Knoten für ein Lemma erstellen
      myDepNode = self.DepNode()
      myDepNode.mapping = mapping
      myDepNode.mapCat = mapCat
      myDepNode.vChild = []
      myDepNode.bActive=True
      myDepNode.bUsed=False
      myDepNode.strRelation=""

      ### Terminal-Knoten aneinanderhängen
      vDepNode.append(myDepNode)

    ### Bottom-Up Regeln anwenden, um einen Parse-Baum zu erhalten
    RootNode = self.apply_collaps_rules(vDepNode)
    if RootNode==None:
      return []

    ### generieren einer Liste von Dependenzrelationen aus dem Parse-Baum
    listInfo=[]
    listInfo = self.generate_mwe_tuples_from_tree( RootNode, mapRelToId, mapRelIdToType )
    
    return listInfo

  def apply_collaps_rules( self, vDepNode ):

    vCollapsRule=[]

    ### Regeln
    myCollapsRule= self.CollapsRule()
    myCollapsRule.strHeadCat=u"Adjektiv"
    myCollapsRule.strDepCat=u"Adverb"
    myCollapsRule.bDepTerminal=True
    myCollapsRule.strRelation=u"ADV"
    myCollapsRule.strDirection="left"
    vCollapsRule.append(myCollapsRule)

    myCollapsRule= self.CollapsRule()
    myCollapsRule.strHeadCat=u"Substantiv"
    myCollapsRule.strDepCat=u"Adjektiv"
    myCollapsRule.bDepTerminal=None
    myCollapsRule.strRelation=u"ATTR"
    myCollapsRule.strDirection="left"
    vCollapsRule.append(myCollapsRule)


    myCollapsRule= self.CollapsRule()
    myCollapsRule.strHeadCat=u"Präposition"
    myCollapsRule.strDepCat=u"Substantiv"
    myCollapsRule.bDepTerminal=None
    myCollapsRule.strRelation=u"PN"
    myCollapsRule.strDirection="right"
    vCollapsRule.append(myCollapsRule)


    myCollapsRule= self.CollapsRule()
    myCollapsRule.strHeadCat=u"Substantiv"
    myCollapsRule.strDepCat=u"Präposition"
    myCollapsRule.bDepTerminal=False
    myCollapsRule.strRelation=u"PP"
    myCollapsRule.strDirection="right"
    vCollapsRule.append(myCollapsRule)

    myCollapsRule= self.CollapsRule()
    myCollapsRule.strHeadCat=u"Verb"
    myCollapsRule.strDepCat=u"Substantiv"
    myCollapsRule.bDepTerminal=None
    myCollapsRule.strRelation=u"SUBJA"
    myCollapsRule.strDirection="left"
    vCollapsRule.append(myCollapsRule)

    myCollapsRule= self.CollapsRule()
    myCollapsRule.strHeadCat=u"Verb"
    myCollapsRule.strDepCat=u"Substantiv"
    myCollapsRule.bDepTerminal=None
    myCollapsRule.strRelation=u"OBJ"
    myCollapsRule.strDirection="right"
    vCollapsRule.append(myCollapsRule)

    myCollapsRule= self.CollapsRule()
    myCollapsRule.strHeadCat=u"Verb"
    myCollapsRule.strDepCat=u"Adverb"
    myCollapsRule.bDepTerminal=True
    myCollapsRule.strRelation=u"ADV"
    myCollapsRule.strDirection="right"
    vCollapsRule.append(myCollapsRule)

    myCollapsRule= self.CollapsRule()
    myCollapsRule.strHeadCat=u"Verb"
    myCollapsRule.strDepCat=u"Präposition"
    myCollapsRule.bDepTerminal=False
    myCollapsRule.strRelation=u"PP"
    myCollapsRule.strDirection="right"
    vCollapsRule.append(myCollapsRule)

    ### einfacher Bottom-Up-Parser
    iCount=0
    bHit=True
    while bHit:
      iCount+=1
      bHit=False
      ### für jede Regel
      for i in range(0,len(vCollapsRule)):
        bHit2=True
        while bHit2:
          bHit2=False
          j=0
          ### Anwenden auf die Eingabe
          while j < len(vDepNode):
            if vCollapsRule[i].strHeadCat in vDepNode[j].mapCat:
        
              ### Linke Anbindung
              if vCollapsRule[i].strDirection=='left' and j>0:
                if vCollapsRule[i].strDepCat in vDepNode[j-1].mapCat and not vDepNode[j-1].bUsed:

                  if vCollapsRule[i].bDepTerminal == (vDepNode[j-1].vChild==[]) or vCollapsRule[i].bDepTerminal==None:
                    vDepNode[j-1].bActive=False
                    vDepNode[j-1].strRelation=vCollapsRule[i].strRelation
                    vDepNode[j].vChild.append(vDepNode[j-1])
                    vDepNode[j].bUsed=True

                    vDepNode[j-1].mapCat = {vCollapsRule[i].strDepCat:vDepNode[j-1].mapCat[vCollapsRule[i].strDepCat]}
                    vDepNode[j].mapCat = {vCollapsRule[i].strHeadCat:vDepNode[j].mapCat[vCollapsRule[i].strHeadCat]}

                    j+=1
                    bHit1=True
                    bHit2=True

              ### Rechte Anbindung
              if vCollapsRule[i].strDirection=='right' and j+1<len(vDepNode):
                if vCollapsRule[i].strDepCat in vDepNode[j+1].mapCat and not vDepNode[j+1].bUsed:
                  if vCollapsRule[i].bDepTerminal == (vDepNode[j+1].vChild==[]) or vCollapsRule[i].bDepTerminal==None:
                    vDepNode[j+1].bActive=False
                    vDepNode[j+1].strRelation=vCollapsRule[i].strRelation
                    vDepNode[j].vChild.append(vDepNode[j+1])
                    vDepNode[j].bUsed=True

                    vDepNode[j+1].mapCat = {vCollapsRule[i].strDepCat:vDepNode[j+1].mapCat[vCollapsRule[i].strDepCat]}
                    vDepNode[j].mapCat = {vCollapsRule[i].strHeadCat:vDepNode[j].mapCat[vCollapsRule[i].strHeadCat]}

                    j+=2
                    bHit1=True
                    bHit2=True

            j+=1
          vDepNodeNew=[]
          for k in vDepNode:
            if k.bActive:
              k.bUsed=False
              vDepNodeNew.append(k)
          vDepNode=vDepNodeNew

    if len(vDepNode)==1:  
      return vDepNode[0]
    
    return None

  """
    Anhand eines Parse-Baums wird eine Liste von Dependenzrelationen erstellt:

    (InformationLemma1, InformationLemma2, Relation, Präposition)

    Wenn keine Präposition involviert ist ist deren Wert -1
  """
  def generate_mwe_tuples_from_tree( self, RootNode, mapRelToId, mapRelIdToType ):

    listInfo=[]
    vStack=[]
    ### durchwandern des Baums
    vStack.append(RootNode)
    while vStack!=[]:
      CurrendNode = vStack.pop()
      mapping1={}
      for i in CurrendNode.mapCat.items():
        mapping1=i[1]
      for i in CurrendNode.vChild:
        ### Id-Liste von nicht-umgedrehten Relationen
        vRel = self.rellist_to_idlist_directed ( [i.strRelation], mapRelToId, mapRelIdToType )
        if i.strRelation=="PP":
          mappingPrep={}
          for j in i.mapCat.items():
            mappingPrep=j[1]
          iPrep=mappingPrep['LemmaId']
          for j in i.vChild:
            for k in j.mapCat.items():
              mapping2=k[1]            
            listInfo.append((mapping1,mapping2,vRel,iPrep))
            vStack.append(j)
        else:
          mapping2={}
          for j in i.mapCat.items():
            mapping2=j[1]
          listInfo.append((mapping1,mapping2,vRel,-1))
          vStack.append(i)
    return listInfo

  """
    Eine Liste von Relationsnamen auf eine Liste von Ids abbilden
  """
  def rellist_to_idlist ( self, listRel, mapRelToId ):
    listRes=[]
    for i in listRel:
      if mapRelToId.has_key(i):
        listRes.append(mapRelToId[i])
    return listRes

  """
    Eine Liste von Relationsnamen auf eine Liste von Ids abbilden, die nicht umgedreht sind (ohne ~)
  """
  def rellist_to_idlist_directed ( self, listRel, mapRelToId, mapRelIdToType ):
    listRes=[]
    for i in listRel:
      if mapRelToId.has_key(i):
        if mapRelIdToType[mapRelToId[i]] != 2:
          listRes.append(mapRelToId[i])
    return listRes



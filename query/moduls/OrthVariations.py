#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import codecs
import sys
import struct

####################################
# Klasse zum Generieren von variierenden Schreibweisen eines Wortes
# 
class OrthVariations:

  mapRepl = {u'ß':u'ss' , u'①':u'ß', u'F':u'Ph', u'②':u'F' , u'f':u'ph', u'③':u'f', u't':u'th', u'T':u'Th', u'④':u'T', u'⑤':u't'}
  mapReplWortende = {u'r@':u'th@', u'é@':'ee@', u'ée@':u'ee@', u'tial@':u'tiell@', u'zial@':u'ziell@'}


  def __generate_variants_base ( self,iPos,strObj,mapRepl ):
	  if iPos >= len(strObj):
		  return [strObj]

	  if mapRepl.has_key(strObj[iPos]):
		  strTo = mapRepl[strObj[iPos]]

		  strNew = strObj[0:iPos]+strTo+strObj[iPos+1:]
		  listRes = []
		  listRes2 = self.__generate_variants_base(iPos+len(strTo),strNew,mapRepl)
		  listRes3 = self.__generate_variants_base(iPos+1,strObj,mapRepl)
		  listRes = listRes + listRes2 + listRes3
		  return listRes
	  else:
		  return self.__generate_variants_base (iPos+1,strObj,mapRepl);

  def generate_variants ( self,strObj,mapRepl ):
	  listResult = []
	  listVariant = self.__generate_variants_base(0,strObj,mapRepl)
	  if (len(listVariant)>1):
		  for j in listVariant:
			  if (j != strObj):
				  listResult.append(j)

	  return listResult


  def gen( self,strSurface ):
    strSurfaceTrans = strSurface.replace(u'ss',u'①').replace(u'Ph',u'②').replace(u'ph',u'③').replace(u'Th',u'④').replace(u'th',u'⑤')

    listVariation = self.generate_variants(strSurfaceTrans,self.mapRepl)

    listVariationFinal=[]
    for i in listVariation:
      listVariationFinal.append(i.replace(u'①',u'ss').replace(u'②',u'Ph').replace(u'③',u'ph').replace(u'④',u'Th').replace(u'⑤',u'th'))
      for j in self.mapReplWortende:
        strVariation = (strSurface+u"@").replace(j,self.mapReplWortende[j])
        strVariation = strVariation.replace(u"@",u"")
        if strSurface != strVariation:
          listVariationFinal.append(strVariation)
    return listVariationFinal


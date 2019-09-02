#!/usr/bin/python
# -*- coding: utf-8 -*-

####################################
# Klasse zum Generieren von variierenden Schreibweisen eines Wortes
# 
class OrthVariations:
    mapRepl = {'ß': 'ss', '①': 'ß', 'F': 'Ph', '②': 'F', 'f': 'ph', '③': 'f', 't': 'th', 'T': 'Th', '④': 'T', '⑤': 't'}
    mapReplWortende = {'r@': 'th@', 'é@': 'ee@', 'ée@': 'ee@', 'tial@': 'tiell@', 'zial@': 'ziell@'}

    def __generate_variants_base(self, iPos, strObj, mapRepl):
        if iPos >= len(strObj):
            return [strObj]

        if strObj[iPos] in mapRepl:
            strTo = mapRepl[strObj[iPos]]

            strNew = strObj[0:iPos] + strTo + strObj[iPos + 1:]
            listRes = []
            listRes2 = self.__generate_variants_base(iPos + len(strTo), strNew, mapRepl)
            listRes3 = self.__generate_variants_base(iPos + 1, strObj, mapRepl)
            listRes = listRes + listRes2 + listRes3
            return listRes
        else:
            return self.__generate_variants_base(iPos + 1, strObj, mapRepl);

    def generate_variants(self, strObj, mapRepl):
        listResult = []
        listVariant = self.__generate_variants_base(0, strObj, mapRepl)
        if (len(listVariant) > 1):
            for j in listVariant:
                if (j != strObj):
                    listResult.append(j)

        return listResult

    def gen(self, strSurface):
        strSurfaceTrans = strSurface.replace('ss', '①').replace('Ph', '②').replace('ph', '③').replace('Th',
                                                                                                      '④').replace('th',
                                                                                                                   '⑤')

        listVariation = self.generate_variants(strSurfaceTrans, self.mapRepl)

        listVariationFinal = []
        for i in listVariation:
            listVariationFinal.append(
                i.replace('①', 'ss').replace('②', 'Ph').replace('③', 'ph').replace('④', 'Th').replace('⑤', 'th'))
            for j in self.mapReplWortende:
                strVariation = (strSurface + "@").replace(j, self.mapReplWortende[j])
                strVariation = strVariation.replace("@", "")
                if strSurface != strVariation:
                    listVariationFinal.append(strVariation)
        return listVariationFinal

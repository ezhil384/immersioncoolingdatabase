# -*- coding: utf-8 -*-
"""
database.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~

ImmersionDataBase data structures.
author: Shu Huang (sh2009@cam.ac.uk)
"""

from chemdataextractor_immersion.chemdataextractor15 import Document
import json
import copy
from chemdataextractor_immersion.chemdataextractor15.model.model import ThermalConductivity, Viscosity, DielectricConstant, FlashPoint


class ImmersionDataBase:

    def __init__(self, paper_root, save_root, filename):
        self.dic = None
        self.filename = filename
        self.paper_root = paper_root
        self.count = 0
        self.save_root = save_root

    def write_into_file(self):
        with open('{}/{}.json'.format(self.save_root, self.filename), 'a', encoding='utf-8') as json_file:
            json.dump(self.dic, json_file, ensure_ascii=False)
            json_file.write('\n')
        return

    def extract(self, file):
        """

        :param file: The parsing files (HTML/XML...)
        :return: Write the record into the documents
        """
        # try:
        f = open(file, 'rb')
        d = Document.from_file(f)
        print('parsing ' + file)
        rough = d.records.serialize()
        data = []
        for dic in rough:
            if 'Compound' in dic:
                continue
            try:
                dic['metadata'] = d.metadata[0].serialize()
                if dic['metadata']['doi'] == "None":
                    pass
            except BaseException:
                pass
            self.count += 1
            if self.is_valid(dic):
                dic_list = self.distribute(dic)
                data += dic_list
        if len(data) <= 3:
            for i in data:
                i['warning'] = 1
        for new_dic in data:
            self.dic = new_dic
            self.write_into_file()
        print(str(self.count) + ' relations in total')
        print(file + ' is done')
        f.close()
        # except BaseException:
        #     pass

    def is_valid(self, dic):
        """
        Check if the data record is valid or not
        :param dic:
        :return:
        """
        try:
                if 'names' in next(iter(dic.values()))['compound']['Compound']:
                    return True
        except BaseException:
                return False

    def distribute(self, dic):
        """
        Extract chemical names if a length of a list > 1

        :param dic: A dictionary returned by CDE
        :return: A list of dictionaries with valid records
        """
        # Create a key 'names' (list)
        name_length = next(iter(dic.values()))['compound']['Compound']['names']
        next(iter(dic.values()))['names'] = [name_length[0]]
        if len(name_length) > 1:
            for j in name_length[1:]:
                if j.lower() not in [x.lower()
                                     for x in next(iter(dic.values()))['names']]:
                    next(iter(dic.values()))['names'].append(j)

        # Update the key 'value' as a list of float
        # next(iter(dic.values()))['value'] = json.loads(
        #     next(iter(dic.values()))['value'])
        val_obj = next(iter(dic.values()))
        if isinstance(val_obj['value'], str):
            val_obj['value'] = json.loads(val_obj['value'])
        # Distribute
        dic_lists = self.distribute_value_and_names(dic)

        return dic_lists

    def distribute_value_and_names(self, dic):
        dic_list = []
        # Extract the actual lists from the dictionary
        val_data = next(iter(dic.values()))
        names = val_data['names']
        values = val_data['value']

        # Ensure values is always a list for consistent iteration
        if not isinstance(values, list):
            values = [values]
        if not isinstance(names, list):
            names = [names]

        len_names = len(names)
        len_values = len(values)

        for name in names:
            for value in values:
                # CRITICAL FIX: If value is still a list, take the last element
                current_val = None if isinstance(value, list) and len(value) == 0 else (value[-1] if isinstance(value, list) else value)
                
                try:
                    copydic = copy.deepcopy(dic)
                    target = next(iter(copydic.values()))
                    target['value'] = float(current_val)
                    target['names'] = name
                    dic_list.append(copydic)
                except (ValueError, TypeError):
                    # Skip values that cannot be converted to float (e.g., None or empty strings)
                    continue
        return dic_list
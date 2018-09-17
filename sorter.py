#!/usr/bin/python3
'''Program to sort all rock band files into folders'''
import sys
import csv
import os.path
import shutil
from glob import glob
from difflib import SequenceMatcher

BEST_MATCH_LOWERS = 0.7999
class RockBandSorter:
    '''CLASS TO SORT ROCK BAND FILES'''
    def __init__(self, input_folder, output_folder):
        print("DATA SETUP....")
        self._input_folder = input_folder
        if self._input_folder[-1] != "/":
            self._input_folder += "/"

        if not os.path.exists(self._input_folder):
            self._input_folder = None
            return

        if output_folder is not None:
            self._output_folder = output_folder
            if not os.path.exists(self._output_folder):
                os.mkdir(self._output_folder)
            if self._output_folder[-1] != "/":
                self._output_folder += "/"

        self._input_file_list = glob(self._input_folder + "*")
        self._dict_of_files = {}

        with open("ROCKBAND.csv", 'r') as open_csv_file:
            self._csv_data = list(csv.DictReader(open_csv_file))

        for item in self._input_file_list:
            tmp_filename = item.rsplit('/', 1)
            print("Sorting file " + tmp_filename + "\r")
            tmp_item = tmp_filename[1].split(" - ")
            if len(tmp_item) == 2:
                artist = tmp_item[0]
                song = tmp_item[1]
            elif len(tmp_item) == 3:
                tmp_artist = self._get_csv_artist(tmp_item[0])
                if tmp_artist is None:
                    artist = tmp_item[0] + " - " + tmp_item[1]
                    song = tmp_item[2]
                else:
                    artist = tmp_item[0]
                    song = tmp_item[1] + " - " + tmp_item[2]
            elif len(tmp_item) == 4:
                special_item = item.rsplit('/', 1)[1].split(" - ", 1)
                artist = special_item[0]
                song = special_item[1]
            else:
                print("ISSUE WITH SONG:", tmp_filename)
                continue

            if not artist in self._dict_of_files:
                self._dict_of_files[artist] = {}
            if not song in self._dict_of_files[artist]:
                self._dict_of_files[artist][song] = item

        print("DATA SETUP DONE")

    def main(self):
        '''the program'''
        if self._input_folder is None:
            print("FAILED INPUT DOESN'T EXIST")
            return

        print("LOOPING THROUGH CSV:", len(self._csv_data))
        match_count = 0
        for item in self._csv_data:
            if item['Got'] == "Yes":
                print('.', end='', flush=True)
                match_count += 1
                continue
            print('*', end='', flush=True)
            item_artist = item['Artist']
            item_song = item['Title']

            use_artist = self._get_artist(item_artist)
            if use_artist is None:
                item['Got'] = "No"
                continue
            use_song = self._get_song(use_artist, item_song)
            #could contain (RB3 version) or (RB2 version)
            if use_song is None:
                use_song = self._get_song(use_artist, item_song + " RB3 version")
                #could contain (RB3 version) or (RB2 version)
                if use_song is None:
                    use_song = self._get_song(use_artist, item_song + " RB2 version")
                    if use_song is None:
                        item['Got'] = "No"
                        continue

            item['Got'] = "Yes"
            match_count += 1
            location = self._dict_of_files.get(use_artist, {}).get(use_song, None)
            if location is None:
                continue
            item['location'] = location
            item['filename'] = item_artist + " - " + item_song
            self._dict_of_files[use_artist][use_song] = item["From"]
        string_count = str(match_count) + "/" + str(len(self._csv_data))
        percent = str(round(match_count / len(self._csv_data) * 100, 2))
        print("\nLOOPED THROUGH CSV AND MATCHED:", string_count, percent + "%")
        print("MOVING FILES INTO FOLDERS")
        self._move_files()
        print("\nMOVED FILES INTO FOLDERS")
        self._write_csv()

    def remove_duplicates(self):
        '''Will remove duplicates/ already in from the input folder but leave any unrecognised'''
        print("SCANNING FOR DUPLICATES")
        got_files = [x['location'] for x in self._csv_data if x['location'] != 'x']
        remove_list = []
        unknown_list = []
        for folder_file in self._input_file_list:

            if folder_file in got_files:
                print('M', end='', flush=True)
                remove_list.append(folder_file)
            else:
                current_best_match = None
                current_best_score = BEST_MATCH_LOWERS
                for input_artist in got_files:
                    tmp_folder_file = folder_file.rsplit('/', 1)[-1]
                    tmp_input_artist = input_artist.rsplit('/', 1)[-1]
                    current_score = SequenceMatcher(None, tmp_folder_file, tmp_input_artist).ratio()
                    if current_score > current_best_score:
                        current_best_match = input_artist
                        current_best_score = current_score
                if current_best_match is None:
                    unknown_list.append(folder_file)
                    print('U', end='', flush=True)
                    continue
                remove_list.append(folder_file)
                print('.', end='', flush=True)
        print("FINISHED SCANNING FOR DUPLICATES")
        print("\nFiles to remove:", len(remove_list))
        print("Unknown Files:", len(unknown_list))
        if remove_list:
            print("REMOVING DUPLICATES")
            for remove_file in remove_list:
                os.remove(remove_file)
            print("REMOVED DUPLICATES")

    def _get_artist(self, in_artist):
        '''Using the name in the DB it will search the folder data and find it or the best match'''
        if in_artist in self._dict_of_files:
            return in_artist

        current_best_match = None
        current_best_score = BEST_MATCH_LOWERS
        for input_artist in self._dict_of_files:
            current_score = SequenceMatcher(None, in_artist, input_artist).ratio()
            if current_score > current_best_score:
                current_best_match = input_artist
                current_best_score = current_score
        return current_best_match

    def _get_csv_artist(self, in_artist):
        '''Using the name in the DB it will search the folder data and find it or the best match'''
        artist_list = [x['Artist'] for x in self._csv_data]
        if in_artist in artist_list:
            return in_artist

        current_best_match = None
        current_best_score = BEST_MATCH_LOWERS
        for csv_artist in artist_list:
            current_score = SequenceMatcher(None, in_artist, csv_artist).ratio()
            if current_score > current_best_score:
                current_best_match = csv_artist
                current_best_score = current_score
        return current_best_match

    def _get_song(self, artist, in_song):
        '''Using the name in the DB it will search the folder data and find it or the best match'''
        if in_song in self._dict_of_files[artist]:
            return in_song

        current_best_match = None
        current_best_score = BEST_MATCH_LOWERS
        for input_song in self._dict_of_files[artist]:
            current_score = SequenceMatcher(None, in_song, input_song).ratio()
            if current_score > current_best_score:
                current_best_match = input_song
                current_best_score = current_score
        return current_best_match

    def _write_csv(self):
        '''writes the csv data back to the file'''
        with open("ROCKBAND.csv", 'w') as open_csv_file:
            csv_obj = csv.DictWriter(open_csv_file, self._csv_data[0].keys())
            csv_obj.writeheader()
            for item in self._csv_data:
                csv_obj.writerow(item)

    def _move_files(self):
        '''moves the files'''
        for item in self._csv_data:
            print('.', end='', flush=True)
            if item["Sorted"] != "Yes":
                if item["Got"] == "Yes":
                    full_output_folder = self._output_folder + item["From"] + "/"
                    if not os.path.exists(full_output_folder):
                        os.mkdir(full_output_folder)
                    full_output_folder += item["filename"]
                    shutil.move(item["location"], full_output_folder)
                    item["Sorted"] = "Yes"
                else:
                    item["Sorted"] = "No"

if __name__ == '__main__':

    if len(sys.argv) == 2:
        SORTER = RockBandSorter(sys.argv[1], None)
        SORTER.remove_duplicates()
    elif len(sys.argv) == 3:
        SORTER = RockBandSorter(sys.argv[1], sys.argv[2])
        SORTER.main()
        SORTER.remove_duplicates()
    else:
        print("USAGE:", sys.argv[0], "[In Folder] [Out Folder]")

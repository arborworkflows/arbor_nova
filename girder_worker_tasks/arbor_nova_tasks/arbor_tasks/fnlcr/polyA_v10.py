from girder_worker.app import app
from girder_worker.utils import girder_job
from tempfile import NamedTemporaryFile

# from polyA_v1 source
import sys
import pathlib
from argparse import ArgumentParser
from pyfaidx import Fasta
from fuzzysearch import find_near_matches
from typing import NamedTuple

# this is just included for reference on how to decorate 
# a function to be called from girder through arbor_nova plugin

#@girder_job(title='PolyA')
#@app.task(bind=True)
#def column_append(self, in_filepath, **kwargs):
#    outname = 'outfile.csv'
#    with open(outname, 'w') as tmp:
#        with open(in_filepath, 'r') as csv:
#            for line in csv:
#                outline = line.strip() + ', newcol\n'
#                tmp.write(outline)
#
#    return outname


class tail_params(NamedTuple):
        idx: int
        header: str
        start: int
        end: int
        len: int
        t_seq: str
        a_seq: str
        l_seq: str
'''  class tail_params lays out the structure for the tail parameters
idx -> sequence number (index) in the Fasta file of sequences
header -> descriptive header for each sequence in Fasta file
start -> base position for the start of the Poly(A) tail in Fasta sequence
len -> length of the Poly(A) tail
t_seq -> last few bases of transcript sequence
a_seq -> Poly(A) tail sequence
l_seq -> beginning of linker sequence
'''

class seed_params(NamedTuple):
    idx: int
    start: int
    stop: int



#
# Define a function to check whether the files exist and print a message if not
#
def file_exists(f,msg):
    path=pathlib.Path(f)
    if(path.is_file() is not True):
        print("The {} file {} does not exist. Please provide a valid {} file.".format(msg,f,msg))
        return False
    else:
        return True
        
#   
# Function 
# Fine Search Left or Right direction with user provided pattern
# Searches moving by 1 character in either left or right direction
#
def fine_search(strt,seq,*,direction='left',pattern='AA',edit_dist=1):
    if (direction == 'left'):
        trim=+2
        shift_left=0
        shift_right=2
        step=-1
    elif (direction == 'right'):
        trim=-2
        shift_left=-2
        shift_right=0
        step=+1
    else:
        print("Direction must be either left or right")
        quit()
    target_seq=seq[strt+shift_left:strt+shift_right]
    match = find_near_matches(pattern, target_seq, max_l_dist=edit_dist)
    while (match):
        strt=strt+step
        target_seq=seq[strt+shift_left:strt+shift_right]
        match = find_near_matches(pattern, target_seq, max_l_dist=edit_dist)
    edge=strt+trim
    return edge

#
# function to find "seed" pattern with a sequence
#
def find_seed(seed, seq, *, hit='last', edit_dist=0):
    match=find_near_matches(seed, seq, max_l_dist=int(edit_dist))
    if match:
        if (hit == 'last'):
            return int(match[len(match)-1].start), int(match[len(match)-1].end)
        elif (hit == 'first'):
            return int(match[0].start), int(match[0].end)
        else:
            return -1, -1
    else:
        return -1, -1
#
# function to Find Linker Sequence
#
def linker_match(linker,seq,edit):
    match = find_near_matches(linker, seq[:], max_l_dist=edit)
    if match:
        return match
    else:
        return None

#
#  Search for Linker
#
# CRL - had to add reference to global linker_seq because not available when running under girder
def find_linker_seqs(linker,seq,start,linker_seq):
    linker_hit=linker_match(linker_seq,seq[start:],0)
    if (linker_hit):
        return linker_hit
    else:
        edit=1
        half_len=int(len(linker_seq)/2)
        while (not linker_hit):
            linker_hit=linker_match(linker_seq,seq[start:],edit)
            edit=edit+1
            if (edit > half_len):
                print("Linker not found for Sequence {:6d}".format(i))
                print("{}".format(seq[start:]))
                break
        if (linker_hit):
            return linker_hit
        else:
            return None

#
# function to Find pattern in Transcript Sequence
#
#def search_transcript(pattern,seq):
def search_transcript(pattern,seq,edit):
    tmatch = find_near_matches(str(pattern), str(seq), max_l_dist=int(edit))
    if tmatch:
        return tmatch[0].start
    else:
        return -1



#-------------------------------------------

@girder_job(title='polyA_v10')
@app.task(bind=True)
def polyA_v10(self,fasta_file,linker_file,transcript_file,**kwargs):

    seeds = []
    tails = []

    print(" fasta filename = {}".format(fasta_file))
    print(" linker filename = {}".format(linker_file))
    print(" transcript filename = {}".format(transcript_file))

    #
    # Check that the Sequence and Linker files exist as files
    #
    if(file_exists(fasta_file,'fasta') is  True): 
        print('found fasta file')
    else:
        print('could not read fasta file')
        quit()
    if(file_exists(linker_file,'linker') is  True): 
        print('found linker file')
    else:
        print('could not read linker file')
        quit()
    if(file_exists(transcript_file,'transcript') is  True): 
        print('found transcript file')
    else:
        print('could not read transcript file')
        quit()

    #
    # Read the Fasta and Linker files using Fasta from pyfaidx
    # and check to see if they are empty
    # If reading any file returns an empty list, then quit()
    #
    fasta = Fasta(fasta_file)
    fasta_headers = []
    fasta_headers = fasta.keys()
    linker = Fasta(linker_file)
    linker_header = []
    linker_header = linker.keys()
    transcript= Fasta(transcript_file)
    transcript_header = []
    transcript_header = transcript.keys()

    
    # if ((len(fasta_headers) == 0) or (len(linker_header) == 0) or (len(transcript_header) == 0)):
    if (not fasta_headers) or (not linker_header) or (not transcript_header):
        print(" One of the input files is either empty or is wrong format.")
        print(" Please check the input files.")
        quit()
    else:
        print(" Sequence file contains {:6d} sequence(s).".format(len(fasta_headers)))
        print(" Linker file contains {:6d} sequence(s).".format(len(linker_header)))
        print(" Transcript file contains {:6d} sequence(s).".format(len(transcript_header)))

    #
    # Read the linker and transcript sequences
    #
    for i, el in enumerate(linker_header,1):
        linker_seq=str(linker[el][5:].seq)
    for i, tr in enumerate(transcript_header,1):
        transcript_seq=str(transcript[tr][:].seq)

    #
    #   START OF LOOPING THROUGH THE SEQUENCES - START OF PROGRAM
    #
    # Search through the sequences to be search for Poly(A) tails
    # examine linker hits to see if it's unique or multiple hits
    #
    for i, h in enumerate(fasta_headers, 1):
        seq=str(fasta[h][:].seq)
        seq_len=len(seq)
        #print("Sequence {:6d} {:6d} bases {}".format(i,seq_len,h))
        linker_matches=find_linker_seqs(linker,seq,0,linker_seq)
        #print(linker_matches)
        if not linker_matches:
            print("Sequence {:6d} - Linker not found".format(i))
            quit()
    #   print("type of linker_matches = {}".format(type(linker_matches)))
        l=0
        seeds.clear()
        #print(seeds)
    #
    # Search for Linker/Poly(A) pairs
    #
        left=0
        right=0

        while (l < len(linker_matches)):

            sstart=int(linker_matches[l].start-20)
    #       print(" type of sstart = {} and value = {:6d}".format(type(sstart),sstart))
            if (sstart < 0):
                seed_info=seed_params(l,-1,-1)
                seeds.append(seed_info)
                break
            else:
                seed_start, seed_stop=find_seed('AAAAAAAAAA',seq[sstart:sstart+20],hit='last',edit_dist=0)
                #print("Seed AAAAAAAAAA seed_start:{:6d} seed_stop:{:6d}".format(seed_start,seed_stop))
                if (seed_start > 0):
                    seed_start=seed_start+sstart
                    seed_stop=seed_stop+sstart
    #               left=fine_search(seed_start,seq,direction='left',pattern='AAAAA',edit_dist=2)
                    left=fine_search(seed_start,seq,direction='left',pattern='AA',edit_dist=1)
    #               left=fine_search(left+2,seq,direction='left',pattern='AA',edit_dist=1)
    #               right=fine_search(seed_stop,seq,direction='right',pattern='AAAAA',edit_dist=2)
                    right=fine_search(seed_stop,seq,direction='right',pattern='AA',edit_dist=1)
    #               right=fine_search(right-2,seq,direction='right',pattern='AA',edit_dist=1)
                    #print("Seed AAAAAAAAAA left:{:6d} right:{:6d}".format(left,right))
                    seed_info=seed_params(l,left,right)
                    seeds.append(seed_info)
                else:
                    seed_start, seed_stop=find_seed('AAAAA',seq[sstart:sstart+20],hit='last',edit_dist=2)
                    #print("Seed AAAAA seed_start:{:6d} seed_stop:{:6d}".format(seed_start,seed_stop))
                    if (seed_start > 0):
                        seed_start=seed_start+sstart
                        seed_stop=seed_stop+sstart
    #                   left=fine_search(seed_start,seq,direction='left',pattern='AAAAA',edit_dist=2)
                        left=fine_search(seed_start,seq,direction='left',pattern='AA',edit_dist=1)
    #                   left=fine_search(left+2,seq,direction='left',pattern='AA',edit_dist=1)
    #                   right=fine_search(seed_stop,seq,direction='right',pattern='AAAAA',edit_dist=2)
                        right=fine_search(seed_stop,seq,direction='right',pattern='AA',edit_dist=1)
    #                   right=fine_search(right-2,seq,direction='right',pattern='AA',edit_dist=1)
                        #print("Seed AAAAA left:{:6d} right:{:6d}".format(left,right))
                        seed_info=seed_params(l,left,right)
                        seeds.append(seed_info)
    #               else:
    #                   seed_info=seed_params(l,-1,-1)
    #                   seeds.append(seed_info)
            l=l+1
        #print("Printing seeds after search")
        #print(seeds)
        num_linkers=l
        l=0
        if seeds:
    # take the closest to the end since that should be the tail (if this isn't correct, it's going to get really complicated
            nseeds=len(seeds)
            seedidx=seeds[len(seeds)-1].idx
            lright=linker_matches[seeds[len(seeds)-1].idx].start-5
            left=seeds[len(seeds)-1].start
            #print("Sequence:{:6d} Header:{} left:{:6d} right:{:6d} nseeds:{:6d} seed_idx:{:6d} lright:{:6d} tail_len:{:6d} tail:{}".format(i,h,left,right,nseeds,seedidx,lright,right-left,seq[left:right]))
            right=linker_matches[seeds[len(seeds)-1].idx].start-5
            tail_info=tail_params(i,h,left+1,right,right-left,seq[left-10:left],seq[left:right],seq[right:right+15])
        else:
    #     No Tail - just take the linker closest to the end
            right=linker_matches[len(linker_matches)-1].start
            left=right
            tail_info=tail_params(i,h,left,right,right-left,seq[left-10:left],' ',seq[right:right+15])
        tails.append(tail_info)
    #
    #  Print the spreadsheet version
    #
    # generate unique names for multiple runs?  Add extension so it is easier to use
    outname = NamedTemporaryFile(delete=False).name+'.csv'

    with open(outname, 'w') as tmp:
        print("Index,Seq_Header,Tail_Start,Tail_End,Tail_Length,Transcript_End,Tail_Seq,Last_2_Tail_seq,Beg_Link_Seq",file=tmp)
        for tail in tails:
            if(tail.len > 1):
                print("{:5d},{},{:5d},{:5d},{:5d},{},{},{},{}".format(tail.idx, tail.header, tail.start, tail.end, tail.len,
                                                                          tail.t_seq, tail.a_seq, tail.a_seq[-2:], tail.l_seq),file=tmp)
            elif(tail.len == 1):
                print("{:5d},{},{:5d},{:5d},{:5d},{},{},{},{}".format(tail.idx, tail.header, tail.start, tail.end, tail.len,
                                                                          tail.t_seq, tail.a_seq, tail.a_seq[-1:], tail.l_seq),file=tmp)
            elif(tail.len == 0):
                print("{:5d},{},{:5d},{:5d},{:5d},{},{},{},{}".format(tail.idx, tail.header, tail.start, tail.end, tail.len,
                                                                          tail.t_seq, tail.a_seq, '', tail.l_seq),file=tmp)
            else:
                print("{:5d},{},{:5d},{:5d},{:5d},{},{},{},{}".format(tail.idx, tail.header, tail.start, tail.end, tail.len,
                                                                          tail.t_seq, tail.a_seq, 'XX', tail.l_seq),file=tmp)

    # return the name of the output file
    return outname


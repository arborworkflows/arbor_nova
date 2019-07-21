from girder_worker.app import app
from girder_worker.utils import girder_job
from tempfile import NamedTemporaryFile

# for task code
import subprocess
import pathlib


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



#-------------------------------------------

@girder_job(title='blastn')
@app.task(bind=True)
def blastn(self,fasta_file,linker_file,**kwargs):

    print(" subject filename = {}".format(fasta_file))
    print(" query filename = {}".format(linker_file))

    #
    # Check that the datafiles exist
    #
    if(file_exists(fasta_file,'fasta') is  True): 
        print('found subject file')
    else:
        print('could not read subject file')
        quit()
    if(file_exists(linker_file,'linker') is  True): 
        print('found query file')
    else:
        print('could not read query file')
        quit()

    # run the command line program as a subprocess and capture the output to return
    outstr = subprocess.run(['/usr/bin/blastn','-subject',fasta_file,'-query',linker_file],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)

    #  Print the output 
    #
    # generate unique names for multiple runs?  Add extension so it is easier to use
    outname = NamedTemporaryFile(delete=False).name+'.txt'

    with open(outname, 'w') as tmp:
        print(outstr,file=tmp)

    # return the name of the output file
    return outname


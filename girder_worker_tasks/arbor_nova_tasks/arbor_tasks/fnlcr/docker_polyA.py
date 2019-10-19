from girder_worker.app import app
from girder_worker.utils import girder_job
from tempfile import NamedTemporaryFile

# for task code
import subprocess
import traceback

#-------------------------------------------

@girder_job(title='docker_polyA')
@app.task(bind=True)
def docker_polyA(self,fasta_file,linker_file,transcript_file,**kwargs):

    print(" subject filename = {}".format(fasta_file))
    print(" query filename = {}".format(linker_file))
    print(" transcript filename = {}".format(transcript_file))

    # run the command line program as a subprocess and capture the output to return
    # if the docker command fails, catch the error and return it in the returned string, which is written to a file when called from a Vue interface.
    try:
        outstr = subprocess.check_output(['/usr/bin/docker', 'run', '-v','/tmp:/tmp', 'jackrcollins/polya_tail:polya_tailfinder','-f',fasta_file,'-l',linker_file,'-t',transcript_file],stderr=subprocess.STDOUT).decode()
        success = True
        print('success running docker\n')
    except Exception as e:
        outstr = traceback.format_exc() 
        success = False
        print('failure running docker\n')
        print('output:')
        print(outstr)

    #  Print the output 
    # generate unique names for multiple runs?  Add extension so it is easier to use
    outname = NamedTemporaryFile(delete=False).name+'.tsv'

    with open(outname, 'w') as tmp:
        print(outstr,file=tmp)

    # return the name of the output file
    return outname

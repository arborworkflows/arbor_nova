from girder_worker.app import app
from girder_worker.utils import girder_job


@girder_job(title='ColumnAppendTask')
@app.task(bind=True)
def column_append(self, in_filepath, **kwargs):
    outname = 'outfile.csv'
    with open(outname, 'w') as tmp:
        with open(in_filepath, 'r') as csv:
            for line in csv:
                outline = line.strip() + ', newcol\n'
                tmp.write(outline)

    return outname

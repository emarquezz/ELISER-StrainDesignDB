import ssl
import urllib.request


from functools import reduce

# SSL context for accessing NCBI FTP over HTTPS
# (certificate verification disabled for compatibility)
SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE


def get_LASER_html(url, record):
        failed = True
        url = url+record+'.txt'
        while failed:
            try:
                html = urllib.request.urlopen(url, context=SSL_CONTEXT)
                failed = False
            except:
                print('Try again ',url)
                
        return(html)
    
def get_tags(papers_sets, database_url):
    
    list_tags = []
    for year in papers_sets:    
        
        papers = [title.split('.txt')[0].split('Record')[1] for title in papers_sets[year]]

        year_url = database_url+year+'/Record'

        for record in papers:
            html = get_LASER_html(year_url, record)
            
            for line in html:
                    line=line.decode().rstrip()
                    tag = line.split('=')[0].rstrip()
                    if tag not in list_tags:
                        list_tags.append(tag)
                        
    full_tags = {'Counts':len(list_tags),
             'Full_list':list_tags,
             'Set':list(set(list_tags))}
                        
    return(full_tags)



def create_primary_tags(papers, record, full_tags):
    #print('***',record,'***')
    for tag in full_tags['Set']:
        if 'Mutant' not in tag:
            papers[record][tag]=None
    
    return(papers)
                              
    
def extract_mutants(papers, tag, value, record):
    muts = tag.split('.')
    dic_mut = reduce(lambda res, cur: {cur: res}, reversed(muts), value)
    
    if len(muts) > 1:
        papers[record][muts[0]] =  papers[record].get(muts[0],{})
        if len(muts) == 2:
            papers[record][muts[0]][muts[1]]= value
            
        elif len(muts)>2:
            papers[record][muts[0]][muts[1]] =  papers[record][muts[0]].get(muts[1],{})
            if len(muts) ==3:
                if ',' not in value and [muts[2]] == 'GeneMutation':
                    papers[record][muts[0]][muts[1]][muts[2]]= {'value':value}
                else:
                    papers[record][muts[0]][muts[1]][muts[2]]={}
                    for mut in value.split(','):
                        papers[record][muts[0]][muts[1]][muts[2]][mut.strip('"')]={}
                        
            elif len(muts)>3:
                papers[record][muts[0]][muts[1]][muts[2]] =  papers[record][muts[0]][muts[1]].get(muts[2],{})
                if len(muts) == 4:
                    #print( papers[record][muts[0]][muts[1]][muts[2]],muts )

                    papers[record][muts[0]][muts[1]][muts[2]][muts[3]]=value
                else:
                    print('FAIL')
                    
    return(papers)
    
def read_LASER_html(html, papers, record):
    numut = None
    
    for line in html:
        line = line.decode().rstrip()
        line = line.split('=')
        
        tag = line[0].strip()
        value = line[1].strip()

        if 'NumberofMutants' in tag:
            numut = int(value.strip('"'))
            for mutant in range(numut):
                papers[record]['Mutant'+str(mutant+1)]={}
                
        elif not(numut) and '_Gonzalez_BetaOxidation' == record:
            numut = 4
            for mutant in range(numut):
                papers[record]['Mutant'+str(mutant+1)]={}
                
        elif numut and 'Mutant' in tag:
            #print(line)
            papers = extract_mutants(papers, tag, value, record)
            
        else:
            papers[record][tag] = value
                
    return(papers)
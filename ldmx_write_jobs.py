#!/usr/bin/env python

import os,sys
import argparse
import subprocess

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

# required arg
parser.add_argument("-c","--config",required=True,type=str,help="Config script to run.")
parser.add_argument("-o","--out_dir",required=True,type=str,help="Directory to copy output to.")
environment = parser.add_mutually_exclusive_group(required=True)
environment.add_argument("--env_script",type=str,default=None,help="Environment script to run before running fire.")
environment.add_argument("--ldmx_version",type=str,default=None,help="LDMX Version to pick a pre-made environment script.")

# optional arg
parser.add_argument("--input_dir",default=None,type=str,help="Directory containing input files to run over.")
parser.add_argument("--num_jobs",type=int,default=None,help="Number of jobs to run (if not input directory given).")
parser.add_argument("--config_args",type=str,default='',help="Extra arguments to be passed to the configuration script.")
parser.add_argument("--start_job",type=int,default=0,help="Starting number to use when counting jobs (and run numbers)")

# rarely-used optional args
parser.add_argument("-t","--test",action='store_true',dest='test',help="Don't submit the job to the batch.")
parser.add_argument("--run_script",type=str,help="Script to run jobs on worker nodes with.",default='%s/run_fire.sh'%os.path.dirname(os.path.realpath(__file__)))
parser.add_argument("--nonice"    , dest="nonice"    , help="Do not run this at nice priority (default nice)", action="store_true")

arg = parser.parse_args()

jobs = 0
if arg.input_dir is not None :
    full_input_dir = os.path.realpath(arg.input_dir)
    inputFileList = os.listdir(arg.input_dir)
    if arg.num_jobs is not None :
        jobs = min(arg.num_jobs,len(inputFileList))
    else :
        jobs = len(inputFileList)
elif arg.num_jobs is not None :
    jobs = arg.num_jobs
else :
    parser.error("Either an input directory of files or a number of jobs needs to be given.")

# make the output directory
full_out_dir_path = os.path.realpath(arg.out_dir)
if not os.path.exists(full_out_dir_path):
    os.makedirs(full_out_dir_path)

if not os.path.exists(full_out_dir_path):
    raise Exception('Unable to create output directory "%s"'%full_out_dir_path)

full_config_path = os.path.realpath(arg.config)
if not os.path.exists(full_config_path) :
    raise Exception('Config script "%s" does not exist.'%full_config_path)

if arg.env_script is not None :
    env_script = os.path.realpath(arg.env_script)
elif arg.ldmx_version is not None :
    env_script = "/local/cms/user/eichl008/ldmx/stable-installs/%s/setup.sh"%arg.ldmx_version
else :
    parser.error('Either a full env script \'--env_script\' or a ldmx_version \'--ldmx_version\' must be specified.')

if not os.path.exists(env_script) :
    raise Exception('Environment script "%s" does not exist.'%env_script)

arguments_template = '{env_script} {config_script} {out_dir} {config_args}'

# Write Condor submit file 
with open('job_list.sub','w') as job_sub_file :
    job_sub_file.write("Executable          =  %s\n"%os.path.realpath(arg.run_script))
    job_sub_file.write("Universe            =  vanilla\n")
    job_sub_file.write("Requirements        =  Arch==\"X86_64\"  &&  (Machine  !=  \"zebra02.spa.umn.edu\")  &&  (Machine  !=  \"zebra03.spa.umn.edu\")  &&  (Machine  !=  \"zebra04.spa.umn.edu\")\n")
    job_sub_file.write("+CondorGroup        =  \"cmsfarm\"\n")
    if not arg.nonice:
        job_sub_file.write("nice_user = True\n")
    job_sub_file.write("Request_Memory      =  1 Gb\n")
    
    for job in range(arg.start_job,arg.start_job+arg.num_jobs) :
        arguments = arguments_template.format(
                env_script = env_script,
                config_script = full_config_path,
                out_dir = full_out_dir_path,
                config_args = "--run_number %d %s"%(job,arg.config_args)
                )

        if arg.input_dir is not None :
            arguments += ' %s'%input_file_list[job-arg.start_job]

        if arg.test :
            job_sub_file.write('output = %s/%d.out\n'%(full_out_dir_path,job))
            job_sub_file.write('error = %s/%d.err\n'%(full_out_dir_path,job))

        job_sub_file.write('arguments = %s\n'%arguments)
        job_sub_file.write('queue\n')
    #end loop over jobs
#submit job list is open

print("Submission setup completed.")

if arg.test:
  quit()

#command = "condor_submit " + condorSubmit.name + "\n"
#subprocess.call(command.split())

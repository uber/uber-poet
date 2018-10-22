import shutil
import os
import dotreader
import subprocess
import logging
import ConfigParser
import json

from cpulogger import CPULog
from moduletree import ModuleNode, ModuleGenType
from os.path import join


def gen_graph(gen_type, dot_path=None, module_count=0):
    app_node, node_list = None, None

    big_modules = 3
    layer_count = 10

    if gen_type == ModuleGenType.flat:
        app_node, node_list = ModuleNode.gen_flat_graph(module_count)
    elif gen_type == ModuleGenType.bs_flat:
        app_node, node_list = ModuleNode.gen_flat_big_small_graph(big_modules, module_count)
    elif gen_type == ModuleGenType.layered:
        app_node, node_list = ModuleNode.gen_layered_graph(layer_count, module_count / layer_count)
    elif gen_type == ModuleGenType.bs_layered:
        app_node, node_list = ModuleNode.gen_layered_big_small_graph(big_modules, module_count)
    elif dot_path and gen_type == ModuleGenType.dot:
        logging.info("Reading dot file: %s", dot_path)
        app_node, node_list = dotreader.DotFileReader().read_dot_file(dot_path)
    else:
        logging.error("Unexpected argument set, aborting.")
        item_list = ', '.join(ModuleGenType.enum_list())
        logging.error("Choose from ({}) module count: {} dot path: {} ".format(item_list, module_count, dot_path))
        raise ValueError("Invalid Arguments")

    return app_node, node_list


def del_old_output_dir(output_directory):
    if os.path.isdir(output_directory):
        logging.warning("Deleting old mock app directory %s", output_directory)
        shutil.rmtree(output_directory)


def make_buckconfig_local(buckconfig_path, build_trace_path, wmo_enabled):
    logging.warn('Overwriting .buckconfig.local file at: %s', buckconfig_path)
    config = ConfigParser.RawConfigParser()
    uber_section = 'uber'
    config.add_section(uber_section)
    config.set(uber_section, 'xcode_tracing_path', build_trace_path)
    config.set(uber_section, 'chrome_trace_build_times', 'true')
    config.set(uber_section, 'whole_module_optimization', str(wmo_enabled))
    config.add_section('project')
    config.set('project', 'ide_force_kill', 'never')

    with open(buckconfig_path, 'w') as buckconfig:
        config.write(buckconfig)


def count_loc(code_path):
    """Returns the number of lines of code in `code_path` using cloc. If cloc is not
    on your system or there is an error, then it returns -1"""
    try:
        logging.info('Counting lines of code in %s', code_path)
        raw_json_out = subprocess.check_output(['cloc', '--quiet', '--json', code_path])
    except OSError:
        logging.warning("You do not have cloc installed, skipping line counting.")
        return -1

    json_out = json.loads(raw_json_out)
    swift_loc = json_out.get('Swift', {}).get('code', 0)
    if not swift_loc:
        logging.error('Unexpected cloc output "%s"', raw_json_out)
        raise ValueError('cloc did not give a correct value')
    return swift_loc


def apply_cpu_to_traces(build_trace_path, cpu_logger):
    # TODO make this only apply to new traces
    logging.info('Applying CPU info to traces in %s', build_trace_path)
    cpu_logs = cpu_logger.process_log()
    trace_paths = [join(build_trace_path, f) for f in os.listdir(build_trace_path) if f.endswith('trace')]
    for trace_path in trace_paths:
        with open(trace_path, 'r') as trace_file:
            traces = json.load(trace_file)
            new_traces = CPULog.apply_log_to_trace(cpu_logs, traces)
        with open(trace_path+'.json', 'w') as new_trace_file:
            json.dump(new_traces, new_trace_file)

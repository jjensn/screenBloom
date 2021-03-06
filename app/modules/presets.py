import hue_interface
import ConfigParser
import utility
import random
import json
import os


def save_new_preset():
    json_to_write = utility.get_config_dict()
    fa_icons = utility.get_fa_class_names()
    icon = random.choice(fa_icons)

    if os.path.isfile(utility.get_json_filepath()):
        with open(utility.get_json_filepath()) as data_file:
            presets = json.load(data_file)

        preset_number = 0
        for key in presets:
            new_preset_number = int(key[key.find('_') + 1:])
            if new_preset_number > preset_number:
                preset_number = new_preset_number
        preset_number = str(preset_number + 1)
        new_key = 'preset_%s' % preset_number
        presets[new_key] = json_to_write
        presets[new_key]['preset_name'] = 'Preset %s' % preset_number
        presets[new_key]['preset_number'] = int(preset_number)
        presets[new_key]['icon_class'] = icon
    else:
        preset_name = 'preset_1'
        preset_number = 1
        json_to_write['preset_name'] = 'Preset 1'
        json_to_write['preset_number'] = preset_number
        json_to_write['icon_class'] = icon
        presets = {
            preset_name: json_to_write
        }

    # Write/Rewrite presets.json with new section
    with open(utility.get_json_filepath(), 'w') as data_file:
        json.dump(presets, data_file)

    print '\nSaved new Preset!'
    return preset_number


def delete_preset(preset_number):
    config = ConfigParser.RawConfigParser()
    config.read(utility.get_config_path())
    current_preset = config.get('Configuration', 'current_preset')

    with open(utility.get_json_filepath()) as data_file:
        presets = json.load(data_file)
        key = 'preset_' + str(preset_number)

        if presets[key]['preset_name'] == current_preset:
            utility.write_config('Configuration', 'current_preset', '')

        del presets[key]

    with open(utility.get_json_filepath(), 'w') as f:
        json.dump(presets, f)

    print '\nDeleted Preset!'


def apply_preset(preset_number):
    with open(utility.get_json_filepath()) as data_file:
        presets = json.load(data_file)

    preset_index = 'preset_' + str(preset_number)
    preset = presets[preset_index]
    utility.write_config('Configuration', 'auto_start', preset['autostart'])
    utility.write_config('Configuration', 'color_mode_enabled', preset['color_mode_enabled'])

    utility.write_config('Light Settings', 'min_bri', preset['min_bri'])
    utility.write_config('Light Settings', 'max_bri', preset['max_bri'])
    utility.write_config('Light Settings', 'black_rgb', preset['black_rgb'])
    utility.write_config('Light Settings', 'update', preset['update'])
    utility.write_config('Light Settings', 'update_buffer', preset['update_buffer'])
    utility.write_config('Light Settings', 'default', preset['default'])
    utility.write_config('Light Settings', 'zone_state', preset['zone_state'])
    utility.write_config('Light Settings', 'zones', preset['zones'])
    utility.write_config('Light Settings', 'active', preset['active'])
    utility.write_config('Light Settings', 'bulb_settings', preset['bulb_settings'])
    utility.write_config('Light Settings', 'display_index', preset['display_index'])
    utility.write_config('Light Settings', 'color_mode', preset['color_mode'])

    utility.write_config('Party Mode', 'running', preset['party_mode'])

    utility.write_config('System Monitoring', 'enabled', preset['system_monitoring_enabled'])
    utility.write_config('System Monitoring', 'mode', preset['system_monitoring_mode'])
    utility.write_config('System Monitoring', 'interval', preset['system_monitoring_interval'])

    utility.write_config('System Monitoring', 'cpu_warning_temp', preset['cpu_warning_temp'])
    utility.write_config('System Monitoring', 'cpu_extreme_temp', preset['cpu_extreme_temp'])
    utility.write_config('System Monitoring', 'cpu_warning_color', preset['cpu_warning_color'])
    utility.write_config('System Monitoring', 'cpu_extreme_color', preset['cpu_extreme_color'])

    utility.write_config('System Monitoring', 'gpu_warning_temp', preset['gpu_warning_temp'])
    utility.write_config('System Monitoring', 'gpu_extreme_temp', preset['gpu_extreme_temp'])
    utility.write_config('System Monitoring', 'gpu_warning_color', preset['gpu_warning_color'])
    utility.write_config('System Monitoring', 'gpu_extreme_color', preset['gpu_extreme_color'])

    return preset


def update_preset(preset_number, preset_name, icon):
    with open(utility.get_json_filepath()) as data_file:
        presets = json.load(data_file)

    preset_to_edit = None
    for preset in presets:
        if int(preset_number) == presets[preset]['preset_number']:
            preset_to_edit = preset

    preset_number = presets[preset_to_edit]['preset_number']
    presets[preset_to_edit] = utility.get_config_dict()
    presets[preset_to_edit]['preset_name'] = preset_name
    presets[preset_to_edit]['icon_class'] = icon
    presets[preset_to_edit]['preset_number'] = preset_number

    with open(utility.get_json_filepath(), 'w') as f:
        json.dump(presets, f)

    print '\nUpdated Preset!'


# Checking to see if current presets need to be updated with new version features
# What madness hath ye wrought with this function -- fix it you idiot!
def update_presets_if_necessary():
    needs_update = False
    config = utility.get_config_dict()
    all_lights = hue_interface.get_lights_list(config['ip'], config['username'])
    all_lights_list = [int(i) for i in all_lights]
    all_lights_str = ','.join([str(i) for i in all_lights_list])

    # Return if presets file does not exist yet
    try:
        with open(utility.get_json_filepath()) as data_file:
            presets = json.load(data_file)
    except IOError:
        return

    current_light_settings = utility.get_current_light_settings()
    presets_to_write = {}
    for preset_name in presets:
        # Check each preset for key errors (new values needing defaults)
        preset = presets[preset_name]
        bulbs = json.loads(preset['bulb_settings'])

        # Check if active bulbs needs to be updated
        active_bulbs = preset['active']
        active_bulbs_list = active_bulbs.split(',')
        new_active_bulbs = []
        for index, bulb_id in enumerate(all_lights_list):
            try:
                bulb = int(active_bulbs_list[index])
                new_active_bulbs.append(bulb)
            except IndexError:
                needs_update = True
                new_active_bulbs.append(0)

        active_bulbs = ','.join([str(i) for i in new_active_bulbs])
        # Add new bulb to current_light_settings if necessary

        for bulb_id in current_light_settings:
            try:
                bulb = bulbs[bulb_id]
            except KeyError:  # Add new bulb with default values
                needs_update = True
                bulb = current_light_settings[bulb_id]
                bulb['max_bri'] = 254
                bulb['min_bri'] = 1
                bulbs[bulb_id] = bulb

        for bulb_id in bulbs:
            bulb = bulbs[bulb_id]
            bulb_current_settings = current_light_settings[str(bulb_id)]

            # Check bulbs for missing key->value pairs here
            try:
                model_id = bulb['model_id']
            except KeyError:
                needs_update = True
                bulb['model_id'] = bulb_current_settings['model_id']
            try:
                gamut = bulb['gamut']
            except KeyError:
                needs_update = True
                bulb['gamut'] = bulb_current_settings['gamut']
            try:
                name = bulb['name']
            except KeyError:
                needs_update = True
                bulb['name'] = bulb_current_settings['name']

        # Version 2.2 Updates #################################################
        try:
            color_mode_enabled = preset['color_mode_enabled']
            system_monitoring_enabled = preset['system_monitoring_enabled']
            system_monitoring_mode = preset['system_monitoring_mode']
            system_monitoring_interval = preset['system_monitoring_interval']
            cpu_warning_temp = preset['cpu_warning_temp']
            cpu_extreme_temp = preset['cpu_extreme_temp']
            cpu_warning_color = preset['cpu_warning_color']
            cpu_extreme_color = preset['cpu_extreme_color']
            gpu_warning_temp = preset['gpu_warning_temp']
            gpu_extreme_temp = preset['gpu_extreme_temp']
            gpu_warning_color = preset['gpu_warning_color']
            gpu_extreme_color = preset['gpu_extreme_color']
        except KeyError:
            needs_update = True
            color_mode_enabled = True
            system_monitoring_enabled = False
            system_monitoring_mode = 'extreme'
            system_monitoring_interval = 5
            cpu_warning_temp = 50
            cpu_extreme_temp = 70
            cpu_warning_color = '255,165,0'
            cpu_extreme_color = '255,0,0'
            gpu_warning_temp = 80
            gpu_extreme_temp = 95
            gpu_warning_color = '255,165,0'
            gpu_extreme_color = '255,0,0'

        if needs_update:
            preset['bulb_settings'] = json.dumps(bulbs)
            preset['active'] = active_bulbs
            preset['all_lights'] = all_lights_str
            preset['color_mode_enabled'] = color_mode_enabled
            preset['system_monitoring_enabled'] = system_monitoring_enabled
            preset['system_monitoring_mode'] = system_monitoring_mode
            preset['system_monitoring_interval'] = system_monitoring_interval
            preset['cpu_warning_temp'] = cpu_warning_temp
            preset['cpu_extreme_temp'] = cpu_extreme_temp
            preset['cpu_warning_color'] = cpu_warning_color
            preset['cpu_extreme_color'] = cpu_extreme_color
            preset['gpu_warning_temp'] = gpu_warning_temp
            preset['gpu_extreme_temp'] = gpu_extreme_temp
            preset['gpu_warning_color'] = gpu_warning_color
            preset['gpu_extreme_color'] = gpu_extreme_color

            presets_to_write[preset_name] = preset

    if needs_update:
        print 'Updating presets...'
        with open(utility.get_json_filepath(), 'w') as f:
            json.dump(presets_to_write, f)

        current_preset = config['current_preset']
        if current_preset:
            for key in presets:
                preset = presets[key]
                name = preset['preset_name']
                if name == current_preset:
                    preset_number = key[key.find('_') + 1:]
                    print 'Applying %s...' % str(key)
                    apply_preset(preset_number)

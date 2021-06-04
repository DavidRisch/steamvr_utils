import log
import pactl_interface


class ConfigHelper:
    def __init__(self, config):
        self.config = config

    def print_help(self):
        help_text = '''
# Because regular expressions can often be unintuitive the following output
# provides help for configuring steamvr_utils to your setup/preferences.

# Recommended procedure:
# - Go to https://regexr.com/ (or a similar site).
# - Copy this entire output in the bottom ("Text") field.
# - Skip to the section for the config value you are interested in or go through all of them one by one.
# - Use the upper ("Expression") field to experiment with the regex until it matches the lines you want.
# - Enter your regex in the config file at ./config/config.yaml
#   (copy from template: cp ./config/config_template.yaml ./config/config.yaml )


# WARNING: For the best results this output should be generated while SteamVR is running!

        '''

        sinks = pactl_interface.Sink.get_all_sinks()

        sink_names = [
            sink.name
            for sink in sinks
        ]

        help_text += '''
# ==== Help for audio:vr_sink_regex and audio:normal_sink_regex ====
# Current value for audio:vr_sink_regex:
{}
# Current value for audio:normal_sink_regex:
{}
# Exactly one line should match each of your regexes.
# Sinks:
{}

'''.format(
            self.config.audio_vr_sink_regex(),
            self.config.audio_normal_sink_regex(),
            '\n'.join(sink_names)
        )

        sources = pactl_interface.Source.get_all_sources()

        source_names = [
            source.name
            for source in sources
        ]

        help_text += '''
# ==== Help for audio:vr_source_regex and audio:normal_source_regex ====
# Current value for audio:vr_source_regex:
{}
# Current value for audio:normal_source_regex:
{}
# Exactly one line should match each of your regexes.
# Sources:
{}

'''.format(
            self.config.audio_vr_source_regex(),
            self.config.audio_normal_source_regex(),
            '\n'.join(source_names)
        )

        card_port_product_names = []
        cards = pactl_interface.Card.get_all_cards()
        for card in cards:
            for port in card.ports:
                if port.product_name is not None:
                    card_port_product_names.append(port.product_name)

        help_text += '''
# ==== Help for audio:card_vr_port_product_name_regex and audio:card_normal_port_product_name_regex ====
# current value for audio:card_vr_port_product_name_regex:
{}
# current value for audio:card_normal_port_product_name_regex:
{}
# Exactly one line should match your regex.
# Card port product names: (SteamVR needs to run for the HMD to show up here)
{}

'''.format(
            self.config.audio_card_port_vr_product_name_regex(),
            self.config.audio_card_port_normal_product_name_regex(),
            '\n'.join(card_port_product_names)
        )

        clients = pactl_interface.Client.get_all_clients()
        client_names = [client.client_name for client in clients]

        help_text += '''
# ==== Help for audio:excluded_clients_regexes ====
# current value for audio:excluded_clients_regexes:
{}
# The lines for each client you want to exclude should be matched by at least one regex.
# Clients:
{}

'''.format(
            '\n'.join(self.config.audio_excluded_clients_regexes()),
            '\n'.join(client_names)
        )

        log.i(help_text)

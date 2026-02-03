import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

class LocalizationProcessor:
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.translation_map = {}
        self.processed_strings = set()

    def generate_fingerprint(self,
                        text: str,
                        file_path: str,
                        context_path: str,
                        event_id: Optional[str] = None,
                        map_id: Optional[str] = None) -> str:
        components = [
            text,
            file_path,
            context_path,
            str(event_id),
            str(map_id)
        ]

        fingerprint_string = '||'.join(components)
        hasher = hashlib.sha256(fingerprint_string.encode('utf-8'))

        return hasher.hexdigest()[:16]

    def process_string(self,
                      text: str,
                      file_path: str,
                      context_path: str,
                      event_id: Optional[str] = None,
                      map_id: Optional[str] = None):
        fingerprint = self.generate_fingerprint(text, file_path, context_path, event_id, map_id)

        self.translation_map[fingerprint] = {
            "original": text,
            "context": {
                "file": file_path,
                "path": context_path,
                "event_id": event_id,
                "map_id": map_id
            }
        }
        self.processed_strings.add(text)

    def process_map_files(self):
        map_path = self.project_path / "data"

        for map_file in map_path.glob("Map???.json"):
            with open(map_file, encoding="utf-8-sig") as f:
                data = json.load(f)
                map_id = map_file.stem[3:]

                for x in data:
                    if x == "displayName":
                        self.process_string(
                            text=data[x],
                            file_path=str(map_file.relative_to(self.project_path)),
                            context_path=f"{map_id}.displayName",
                            event_id=None,
                            map_id=map_id
                        )

                if "events" not in data:
                    continue

                for event_idx, event in enumerate(data["events"]):
                    if event is None:
                        continue

                    for page_idx, page in enumerate(event["pages"]):
                        for list_idx, item in enumerate(page["list"]):
                            if item["code"] == 401:
                                self.process_string(
                                    text=item["parameters"][0],
                                    file_path=str(map_file.relative_to(self.project_path)),
                                    context_path=f"events.{event_idx}.pages.{page_idx}.list.{list_idx}.parameters.0",
                                    event_id=str(event_idx),
                                    map_id=map_id
                                )
                            elif item["code"] == 102:
                                for choice_idx, choice in enumerate(item["parameters"][0]):
                                    self.process_string(
                                        text=choice,
                                        file_path=str(map_file.relative_to(self.project_path)),
                                        context_path=f"events.{event_idx}.pages.{page_idx}.list.{list_idx}.parameters.0.{choice_idx}",
                                        event_id=str(event_idx),
                                        map_id=map_id
                                    )

    def process_custom_file(self, file_name: str, path_extractors: list):
        possible_paths = [
            self.project_path / "data" / file_name,
            self.project_path / file_name,
            Path("data") / file_name,
            Path(file_name)
        ]

        file_path = None
        for path in possible_paths:
            if path.exists():
                file_path = path
                break

        if file_path is None:
            raise FileNotFoundError(f"Could not find {file_name} in any of these locations: {possible_paths}")

        with open(file_path, encoding="utf-8-sig") as f:
            data = json.load(f)

            for extractor in path_extractors:
                for text, context_path in extractor(data):
                    self.process_string(
                        text=text,
                        file_path=str(file_path.relative_to(self.project_path) if self.project_path in file_path.parents else str(file_path)),
                        context_path=context_path
                    )

    def save_translation_map(self, output_file: str):
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.translation_map, f, ensure_ascii=False, indent=2)

def extract_from_common_events(data: list):
    results = []
    for idx, event in enumerate(data):
        if event is None:
            continue

        if "name" in event and event["name"]:
            results.append((event["name"], f"{idx}.name"))

        if "list" not in event:
            continue

        for list_idx, item in enumerate(event["list"]):
            if item["code"] == 401:
                results.append((
                    item["parameters"][0],
                    f"{idx}.list.{list_idx}.parameters.0"
                ))
            elif item["code"] == 102:
                for choice_idx, choice in enumerate(item["parameters"][0]):
                    results.append((
                        choice,
                        f"{idx}.list.{list_idx}.parameters.0.{choice_idx}"
                    ))
    return results

def extract_from_items(data: list):
    results = []
    for idx, item in enumerate(data):
        if item and "name" in item:
            results.append((item["name"], f"{idx}.name"))
        if item and "description" in item:
            results.append((item["description"], f"{idx}.description"))
    return results

def extract_from_actors(data: list):
    results = []
    for idx, actor in enumerate(data):
        if actor and "name" in actor:
            results.append((actor["name"], f"{idx}.name"))
        if actor and "profile" in actor:
            results.append((actor["profile"], f"{idx}.profile"))
    return results

def extract_from_classes(data: list):
    results = []
    for idx, class_data in enumerate(data):
        if class_data and "name" in class_data:
            results.append((class_data["name"], f"{idx}.name"))
    return results

def extract_from_skills(data: list):
    results = []
    for idx, skill in enumerate(data):
        if skill:
            if "name" in skill:
                results.append((skill["name"], f"{idx}.name"))
            if "description" in skill:
                results.append((skill["description"], f"{idx}.description"))
            if "message1" in skill:
                results.append((skill["message1"], f"{idx}.message1"))
            if "message2" in skill:
                results.append((skill["message2"], f"{idx}.message2"))
    return results

def extract_from_states(data: list):
    results = []
    for idx, state in enumerate(data):
        if state:
            if "name" in state:
                results.append((state["name"], f"{idx}.name"))
            if "message1" in state:
                results.append((state["message1"], f"{idx}.message1"))
            if "message2" in state:
                results.append((state["message2"], f"{idx}.message2"))
            if "message3" in state:
                results.append((state["message3"], f"{idx}.message3"))
            if "message4" in state:
                results.append((state["message4"], f"{idx}.message4"))
    return results

def extract_from_system(data: dict):
    results = []

    terms = data.get("terms", {})
    if isinstance(terms, dict):
        basic = terms.get("basic", [])
        if isinstance(basic, list):
            for idx, term in enumerate(basic):
                if term:
                    results.append((term, f"terms.basic.{idx}"))

        commands = terms.get("commands", [])
        if isinstance(commands, list):
            for idx, command in enumerate(commands):
                if command:
                    results.append((command, f"terms.commands.{idx}"))

        params = terms.get("params", [])
        if isinstance(params, list):
            for idx, param in enumerate(params):
                if param:
                    results.append((param, f"terms.params.{idx}"))

        messages = terms.get("messages", {})
        if isinstance(messages, dict):
            for key, message in messages.items():
                if message:
                    results.append((message, f"terms.messages.{key}"))

    if "gameTitle" in data:
        results.append((data["gameTitle"], "gameTitle"))

    if "currencyUnit" in data:
        results.append((data["currencyUnit"], "currencyUnit"))

    return results

def extract_from_weapons(data: list):
    results = []
    for idx, weapon in enumerate(data):
        if weapon:
            if "name" in weapon:
                results.append((weapon["name"], f"{idx}.name"))
            if "description" in weapon:
                results.append((weapon["description"], f"{idx}.description"))
    return results

def extract_from_armors(data: list):
    results = []
    for idx, armor in enumerate(data):
        if armor:
            if "name" in armor:
                results.append((armor["name"], f"{idx}.name"))
            if "description" in armor:
                results.append((armor["description"], f"{idx}.description"))
    return results

def extract_from_enemies(data: list):
    results = []
    for idx, enemy in enumerate(data):
        if enemy and "name" in enemy:
            results.append((enemy["name"], f"{idx}.name"))
    return results

def extract_from_troops(data: list):
    results = []
    for idx, troop in enumerate(data):
        if troop and "name" in troop:
            results.append((troop["name"], f"{idx}.name"))
    return results

def extract_from_misc(data: dict):
    results = []
    for item in data.get("misc_strings", []):
        if "text" in item and "id" in item:
            context_path = f"misc.{item['id']}"
            results.append((item["text"], context_path))
    return results


class LocalizationPatcher:
    def __init__(self, project_path: str, translation_map_file: str, language: str):
        self.project_path = Path(project_path)
        self.language = language

        with open(translation_map_file, encoding='utf-8') as f:
            self.translation_map = json.load(f)

    def patch_file(self, file_path: Path, patches: Dict[str, Any]):
        """Generic file patcher that applies patches based on JSON paths"""
        with open(file_path, encoding='utf-8-sig') as f:
            data = json.load(f)

        for path, new_text in patches.items():
            components = path.split('.')

            target = data
            for i, comp in enumerate(components[:-1]):
                if comp.isdigit():
                    comp = int(comp)
                target = target[comp]

            last_comp = components[-1]
            if last_comp.isdigit():
                last_comp = int(last_comp)
            target[last_comp] = new_text

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def patch_all_files(self):
        file_patches = {}

        for fingerprint, entry in self.translation_map.items():
            if self.language not in entry.get("translations", {}):
                continue

            translated_text = entry["translations"][self.language]
            file_path = entry["context"]["file"]
            context_path = entry["context"]["path"]

            if file_path not in file_patches:
                file_patches[file_path] = {}

            file_patches[file_path][context_path] = translated_text

        for file_path, patches in file_patches.items():
            full_path = self.project_path / file_path
            print(f"   [*] patching {file_path}...")
            if "rmmvlt_misc.json" in file_path:
                self.patch_misc_file(full_path, patches)
            else:
                self.patch_file(full_path, patches)
    
    def patch_misc_file(self, file_path: Path, patches: Dict[str, Any]):
        with open(file_path, encoding='utf-8-sig') as f:
            data = json.load(f)

        for path, new_text in patches.items():
            if path.startswith("misc."):
                target_id = path[5:]
                for item in data.get("misc_strings", []):
                    if item.get("id") == target_id:
                        item["text"] = new_text
                        break

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

DEFAULT_STRINGS_FILE = 'rmmvlt.json'


def create_parser():
    parser = argparse.ArgumentParser(description='RPGMaker MV Localization Thingy')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # init command: project -> strings.json
    init_parser = subparsers.add_parser('init', help='Scan project and create strings file')
    init_parser.add_argument('-p', '--project', default='.',
                             help='Path to RPGMaker project directory (default: current directory)')
    init_parser.add_argument('-o', '--output', default=DEFAULT_STRINGS_FILE,
                             help=f'Output strings file (default: {DEFAULT_STRINGS_FILE})')

    # export command: strings.json -> excel
    export_parser = subparsers.add_parser('export', help='Export strings to Excel for translation')
    export_parser.add_argument('strings_file', nargs='?', default=DEFAULT_STRINGS_FILE,
                               help=f'Strings file to export (default: {DEFAULT_STRINGS_FILE})')
    export_parser.add_argument('-o', '--output', metavar='XLSX',
                               help='Output Excel file (default: <strings_file>.xlsx)')
    export_parser.add_argument('-l', '--language', required=True,
                               help='Language code to export (e.g., ja, en, fr)')

    # import command: excel -> strings.json
    import_parser = subparsers.add_parser('import', help='Import translated Excel back into strings file')
    import_parser.add_argument('excel_file',
                               help='Excel file to import')
    import_parser.add_argument('-s', '--strings', default=DEFAULT_STRINGS_FILE,
                               help=f'Strings file to update (default: {DEFAULT_STRINGS_FILE})')
    import_parser.add_argument('-o', '--output',
                               help='Output strings file (default: update input file)')
    import_parser.add_argument('-l', '--language', required=True,
                               help='Language code being imported (e.g., ja, en, fr)')

    # patch command: strings.json -> project
    patch_parser = subparsers.add_parser('patch', help='Apply translations to project files')
    patch_parser.add_argument('-s', '--strings', default=DEFAULT_STRINGS_FILE,
                              help=f'Strings file to use (default: {DEFAULT_STRINGS_FILE})')
    patch_parser.add_argument('-p', '--project', default='.',
                              help='Path to RPGMaker project directory (default: current directory)')
    patch_parser.add_argument('-l', '--language', required=True,
                              help='Language code to patch (e.g., ja, en, fr)')

    return parser

def translation_map_to_excel(translation_map_file: str, output_excel: str, language: str):
    with open(translation_map_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    grouped_data = {}

    for fingerprint, entry in data.items():
        original_text = entry['original'].strip()

        if not original_text:
            continue

        if original_text not in grouped_data:
            grouped_data[original_text] = {
                'fingerprints': [],
                'contexts': [],
                'translation': entry.get('translations', {}).get(language, ''),
                'first_context': None
            }

        context = entry['context']['file']

        if 'MapInfos.json' in context:
            map_id = entry['context']['path'].split('.')[0]
            context_str = f"Map Name: {map_id}"
        elif 'Map' in context:
            map_id = entry['context'].get('map_id', '0')
            event_id = entry['context'].get('event_id', '0')

            if not event_id or event_id == "-1":
                context_str = f"Map {map_id} Display Name"
            else:
                context_str = f"Map {map_id} Event {event_id}"

            if grouped_data[original_text]['first_context'] is None:
                grouped_data[original_text]['first_context'] = (int(map_id), int(event_id) if event_id else 0)
        else:
            context_str = f"{context}: {entry['context']['path']}"

        grouped_data[original_text]['fingerprints'].append(fingerprint)
        grouped_data[original_text]['contexts'].append(context_str)

    excel_data = []

    map_data = []
    other_data = []

    for original_text, group in grouped_data.items():
        fingerprints = '; '.join(group['fingerprints'])

        context_counts = {}
        for ctx in group['contexts']:
            context_counts[ctx] = context_counts.get(ctx, 0) + 1

        formatted_contexts = []
        for ctx, count in context_counts.items():
            if count > 1:
                formatted_contexts.append(f"{ctx} (×{count})")
            else:
                formatted_contexts.append(ctx)

        contexts = ' | '.join(formatted_contexts)

        row = {
            'Fingerprint': fingerprints,
            'Context': contexts,
            'Original Text': original_text,
            f'{language} Translation': group['translation'],
            'Comment': ''
        }

        if group['first_context'] is not None:
            map_id, event_id = group['first_context']
            row['_sort_key'] = (map_id * 10000) + event_id
            map_data.append(row)
        else:
            other_data.append(row)

    map_data.sort(key=lambda x: x['_sort_key'])

    excel_data = map_data + other_data

    for row in excel_data:
        if '_sort_key' in row:
            del row['_sort_key']

    df = pd.DataFrame(excel_data)
    df.to_excel(output_excel, index=False)
    print(f"   [*] excel file created: {output_excel}")

def excel_to_translation_map(excel_file: str, original_map_file: str, output_map_file: str, language: str):
    with open(original_map_file, 'r', encoding='utf-8') as f:
        translation_map = json.load(f)

    df = pd.read_excel(excel_file, dtype={'Fingerprint': str})

    processed = 0
    skipped = 0

    for _, row in df.iterrows():
        raw_fingerprints = str(row['Fingerprint'])
        fingerprints = [fp.strip() for fp in raw_fingerprints.split(';') if fp.strip()]
        translated_text = row[f'{language} Translation']

        if pd.notna(translated_text):
            for fingerprint in fingerprints:
                if fingerprint in translation_map:
                    if 'translations' not in translation_map[fingerprint]:
                        translation_map[fingerprint]['translations'] = {}
                    translation_map[fingerprint]['translations'][language] = str(translated_text)
                    processed += 1
                else:
                    print(f"   [!] warning: fingerprint not found in map: {fingerprint}")
                    skipped += 1

    print(f"   [*] processed {processed} translations")
    if skipped > 0:
        print(f"   [!] skipped {skipped} invalid fingerprints")

    with open(output_map_file, 'w', encoding='utf-8') as f:
        json.dump(translation_map, f, ensure_ascii=False, indent=2)

    print(f"   [*] translation map created: {output_map_file}")

def print_banner():
    banner = """
            ██████
        ████▒▒░░░░██              ████
      ██▒▒░░░░░░░░░░██          ██░░██
    ██░░░░░░░░░░▒▒▒▒▒▒██      ██▒▒░░██
    ██░░░░░░░░██████▒▒██      ██░░░░██
  ██▒▒░░░░░░▒▒██▓▓░░▒▒██    ██▒▒░░██
  ██░░░░░░▒▒▒▒██░░░░██    ██▒▒▒▒░░██
██░░░░░░░░▒▒▒▒▒▒▒▒▓▓▒▒████▓▓▒▒▒▒▒▒██
██░░░░░░▒▒▓▓▒▒▓▓▓▓▒▒▒▒▒▒▒▒▓▓▓▓▒▒██
  ██▓▓▒▒▓▓▓▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓▓████
    ████▒▒▓▓░░░░▒▒▒▒▒▒▒▒▓▓▓▓██
      ██▓▓░░░░░░░░▒▒▒▒▓▓░░▒▒▒▒██
    ██▒▒▓▓▒▒▒▒░░░░░░▓▓░░░░░░▒▒▓▓██
    ██▒▒▒▒▓▓██▒▒▒▒▒▒▓▓░░░░░░▒▒▒▒██
      ██████  ██████░░░░░░▒▒▒▒██
                  ██▒▒░░░░▒▒██
                    ██▒▒▒▒██
                      ████
    """
    print(banner)
    print("======================================")
    print("|| RPG Maker MV Localization Thingy ||")
    print("||                                  ||")
    print("||    made with love by             ||")
    print("||               aria unicornfan    ||")
    print("======================================")
    print()

def print_success(message):
    print(f"\n[@] {message}")
    print("[@] operation success")
    print()

def extract_strings(project_path: str, output_file: str):
    """Extract all translatable strings from a project into a strings file."""
    print("[>] initializing")
    processor = LocalizationProcessor(project_path)

    print("\n[>] processing maps")
    processor.process_map_files()

    print("\n[>] processing datafiles")
    data_files = [
        ("Items.json", [extract_from_items]),
        ("Actors.json", [extract_from_actors]),
        ("Classes.json", [extract_from_classes]),
        ("Skills.json", [extract_from_skills]),
        ("States.json", [extract_from_states]),
        ("System.json", [extract_from_system]),
        ("Weapons.json", [extract_from_weapons]),
        ("Armors.json", [extract_from_armors]),
        ("Enemies.json", [extract_from_enemies]),
        ("CommonEvents.json", [extract_from_common_events]),
    ]

    for filename, extractors in data_files:
        try:
            print(f"   [*] reading {filename}...")
            processor.process_custom_file(filename, extractors)
        except FileNotFoundError:
            print(f"   [~] {filename} not found, skipping...")
        except Exception as e:
            print(f"   [!] error processing {filename}: {e}")

    # try to process misc strings if file exists
    try:
        print("\n[>] processing rmmvlt_misc.json...")
        processor.process_custom_file("rmmvlt_misc.json", [extract_from_misc])
        print("   [*] processed misc strings")
    except FileNotFoundError:
        print("   [~] no rmmvlt_misc.json found, skipping misc strings...")
    except Exception as e:
        print(f"   [!] error processing rmmvlt_misc.json: {e}")

    print(f"\n[>] creating strings file: {output_file}")
    processor.save_translation_map(output_file)
    print_success("extraction complete")


def main():
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    print_banner()

    if args.command == 'init':
        extract_strings(args.project, args.output)

    elif args.command == 'export':
        excel_file = args.output
        if not excel_file:
            # Default to same name as strings file but with .xlsx extension
            base = Path(args.strings_file).stem
            excel_file = f"{base}.xlsx"

        print(f"[>] exporting {args.strings_file} -> {excel_file}")
        translation_map_to_excel(args.strings_file, excel_file, args.language)
        print_success("export complete")

    elif args.command == 'import':
        output_file = args.output or args.strings

        print(f"[>] importing {args.excel_file} -> {output_file}")
        excel_to_translation_map(args.excel_file, args.strings, output_file, args.language)
        print_success("import complete")

    elif args.command == 'patch':
        print(f"[>] patching project with language: {args.language}")
        patcher = LocalizationPatcher(args.project, args.strings, args.language)

        try:
            patcher.patch_all_files()
            print_success("patching complete!")
        except Exception as e:
            print(f"[!] error during patching: {e}")
            return


if __name__ == "__main__":
    main()

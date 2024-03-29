import re
import requests


def parse(text):
    display = []
    for match in re.findall(r"id=\".*?\">\"(.*?)\"</code>\n.*\n.*<td>(((.*?)\n)+?)\s+(<tr>|</table>)", text):
        doc = re.sub(r"[ \t][ \t]+", "\n", match[1])
        doc = re.sub(r"<a .*?>(.*?)</a>", "\\1", doc)
        doc_comment = ""
        for line in doc.split('\n'):
            line = line.strip()
            if not line:
                continue
            doc_comment += "    /// {}\n".format(line)
        display.append([match[0], doc_comment, []])
    return display


def emit_enum_entries(display, file):
    for [key, doc_comment, alternatives] in display:
        print("{}    {},".format(doc_comment, key), file=file)


def print_display_entries(display, file):
    for [key, doc_comment, alternatives] in display:
        print("            {0} => f.write_str(\"{0}\"),".format(
            key), file=file)


def print_from_str_entries(display, file):
    for [key, doc_comment, alternatives] in display:
        print("            \"{0}\"".format(key), file=file, end='')
        for alternative in alternatives:
            print(" | \"{0}\"".format(alternative), file=file, end='')
        print(" => Ok({0}),".format(key), file=file)


def add_alternative_for(display, key, alternative):
    for [found_key, doc_comment, alternatives] in display:
        if found_key != key:
            continue
        alternatives.append(alternative)


def convert_key(text, file):
    print("""
// AUTO GENERATED CODE - DO NOT EDIT

use core::fmt::{self, Display};

#[cfg(feature = "std")]
use std::error::Error;

/// Key represents the meaning of a keypress.
///
/// Specification:
/// <https://w3c.github.io/uievents-key/>
#[derive(Clone, Debug, Eq, PartialEq, Hash, PartialOrd, Ord, Copy)]
#[cfg_attr(feature = "serde", derive(serde::Serialize, serde::Deserialize))]
#[non_exhaustive]
pub enum Key<'a> {
    /// A key string that corresponds to the character typed by the user,
    /// taking into account the user’s current locale setting, modifier state,
    /// and any system-level keyboard mapping overrides that are in effect.
    Character(&'a str),
    """, file=file)
    display = parse(text)

    for i in range(13, 25):
        display.append([
            'F{}'.format(i),
            '    /// The F{0} key, a general purpose function key, as index {0}.\n'.format(i),
            []
        ])

    emit_enum_entries(display, file)
    print("}", file=file)

    print("""

impl Display for Key<'_> {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        use self::Key::*;
        match *self {
            Character(s) => f.write_str(s),
    """, file=file)
    print_display_entries(display, file)
    print("""
        }
    }
}

impl<'a> Key<'a> {
    /// Parse this `Key` from a string.
    pub fn parse(s: &'a str) -> Result<Self, UnrecognizedKeyError> {
        use Key::*;
        match s {
            s if is_key_string(s) => Ok(Character(s)),""", file=file)
    print_from_str_entries(display, file)
    print("""
            _ => Err(UnrecognizedKeyError),
        }
    }
}

/// Parse from string error, returned when string does not match to any Key variant.
#[derive(Clone, Debug)]
pub struct UnrecognizedKeyError;

impl fmt::Display for UnrecognizedKeyError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "Unrecognized key")
    }
}

#[cfg(feature = "std")]
impl Error for UnrecognizedKeyError {}

/// Check if string can be used as a `Key::Character` _keystring_.
///
/// This check is simple and is meant to prevents common mistakes like mistyped keynames
/// (e.g. `Ennter`) from being recognized as characters.
fn is_key_string(s: &str) -> bool {
    s.chars().all(|c| !c.is_control()) && s.chars().skip(1).all(|c| !c.is_ascii())
}

#[cfg(test)]
mod test {
    use super::*;

    #[test]
    fn test_is_key_string() {
        assert!(is_key_string("A"));
        assert!(!is_key_string("AA"));
        assert!(!is_key_string("\t"));
    }
}
    """, file=file)


def convert_code(text, file):
    print("""
// AUTO GENERATED CODE - DO NOT EDIT

use core::fmt::{self, Display};
use core::str::FromStr;

#[cfg(feature = "std")]
use std::error::Error;

/// Code is the physical position of a key.
///
/// The names are based on the US keyboard. If the key
/// is not present on US keyboards a name from another
/// layout is used.
///
/// Specification:
/// <https://w3c.github.io/uievents-code/>
#[derive(Copy, Clone, Debug, Eq, PartialEq, Hash, PartialOrd, Ord)]
#[cfg_attr(feature = "serde", derive(serde::Serialize, serde::Deserialize))]
#[non_exhaustive]
pub enum Code {""", file=file)
    display = parse(text)

    for i in range(13, 25):
        display.append([
            'F{}'.format(i),
            '    /// <code class="keycap">F{}</code>\n'.format(i),
            []
        ])

    chromium_key_codes = [
        'BrightnessDown',
        'BrightnessUp',
        'DisplayToggleIntExt',
        'KeyboardLayoutSelect',
        'LaunchAssistant',
        'LaunchControlPanel',
        'LaunchScreenSaver',
        'MailForward',
        'MailReply',
        'MailSend',
        'MediaFastForward',
        'MediaPause',
        'MediaPlay',
        'MediaRecord',
        'MediaRewind',
        'MicrophoneMuteToggle',
        'PrivacyScreenToggle',
        'SelectTask',
        'ShowAllWindows',
        'ZoomToggle',
    ]

    for chromium_only in chromium_key_codes:
        display.append([
            chromium_only,
            '    /// Non-standard code value supported by Chromium.\n',
            []
        ])

    add_alternative_for(display, 'MetaLeft', 'OSLeft')
    add_alternative_for(display, 'MetaRight', 'OSRight')
    add_alternative_for(display, 'AudioVolumeDown', 'VolumeDown')
    add_alternative_for(display, 'AudioVolumeMute', 'VolumeMute')
    add_alternative_for(display, 'AudioVolumeUp', 'VolumeUp')
    add_alternative_for(display, 'MediaSelect', 'LaunchMediaPlayer')

    emit_enum_entries(display, file)
    print("}", file=file)

    print("""

impl Display for Code {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        use self::Code::*;
        match *self {
    """, file=file)
    print_display_entries(display, file)
    print("""
        }
    }
}

impl FromStr for Code {
    type Err = UnrecognizedCodeError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        use Code::*;
        match s {""", file=file)
    print_from_str_entries(display, file)
    print("""
            _ => Err(UnrecognizedCodeError),
        }
    }
}

/// Parse from string error, returned when string does not match to any Code variant.
#[derive(Clone, Debug)]
pub struct UnrecognizedCodeError;

impl fmt::Display for UnrecognizedCodeError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "Unrecognized code")
    }
}

#[cfg(feature = "std")]
impl Error for UnrecognizedCodeError {}
    """, file=file)


if __name__ == '__main__':
    input = requests.get('https://w3c.github.io/uievents-key/').text
    with open('src/key.rs', 'w', encoding='utf-8') as output:
        convert_key(input, output)
    input = requests.get('https://w3c.github.io/uievents-code/').text
    with open('src/code.rs', 'w', encoding='utf-8') as output:
        convert_code(input, output)

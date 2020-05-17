import sys
import textwrap

# Output a binary file which a ESCPOS thermal printer will understand
# References:
#  - Command manual PDF, in this repository
#  - https://www.neodynamic.com/articles/How-to-print-raw-ESC-POS-commands-from-Javascript/

outputFilename = "output.bin"

esc = '\x1B'; # ESC byte in hex notation
newLine = '\x0A'; # LF byte in hex notation

# Emphasized + Double-height + Double-width mode selected (ESC ! (8 + 16 + 32)) 56 dec => 38 hex
TextStyle_Large = '\x38'
TextStyle_DoubleWidth = '\x20'
TextStyle_RegularEmphasis = '\x08' # Regular size + emphasis (0 + 8)
TextStyle_Regular = '\x00'

# Format specifier, column width
lineWrapColumns = {TextStyle_Large:16, TextStyle_DoubleWidth:16,
                   TextStyle_RegularEmphasis:32, TextStyle_Regular:32}

gOutputBuffer = ''
gCurrentTextStyle = TextStyle_Regular

def writeOutputBuffer():
    global gOutputBuffer
    encodedString = gOutputBuffer.encode("ascii")
    # I think the printer needs to be told this is the desired format
    # encodedString = gOutputBuffer.encode("gb18030")
    print("Outputting to {}".format(outputFilename))
    print("Use the following command (replacing [your printer]) to print:\n"
          "lpr -P [your printer] output.bin")
    outFile = open(outputFilename, "wb")
    outFile.write(encodedString)
    outFile.close()

def setTextStyle(styleSpecifier):
    global gCurrentTextStyle
    if styleSpecifier not in lineWrapColumns:
        print("Warning: style specifier '{}' not fully supported".format(styleSpecifier))

    outputRaw(esc + '!' + styleSpecifier)
    gCurrentTextStyle = styleSpecifier

def outputInitializationCode():
    # Initializes the printer (ESC @)
    outputRaw(esc + "@")
    setTextStyle(TextStyle_Regular)

# Don't fix up newlines or anything
def outputRaw(outString):
    global gOutputBuffer
    gOutputBuffer += outString

# Wrap lines and convert newlines to the appropriate format character
# TODO: Make empty lines newlines still show up instead of being removed by this
def outputTextBlock(outString):
    global gOutputBuffer

    wrapWidth = lineWrapColumns[gCurrentTextStyle]
    # Fix newlines and wrap
    # lines = outString.replace('\n', newLine).split(newLine)
    # We will be adding this newline later, and it will just confuse the splitter.
    if outString[-1] == '\n':
        outString = outString[:-1]
    lines = outString.split("\n")
    wrappedLines = []
    for line in lines:
        if not line:
            wrappedLines.append('')
        wrappedLines += textwrap.wrap(line, width=wrapWidth)
    # exit()
    for line in wrappedLines:
        if line:
            gOutputBuffer += line + newLine
        else:
            gOutputBuffer += newLine

def lineHasTagExactly(line, tag):
    return len(line) >= len(tag) and tag in line[:len(tag)]

def lineGetTaggedValue(line, tag):
    return line[len(tag):]

def orgModeToEscPos(orgLines):
    for line in orgLines:
        if lineHasTagExactly(line, '#+TITLE:'):
            setTextStyle(TextStyle_Large)
            outputTextBlock("\n" + lineGetTaggedValue(line, '#+TITLE:'))
        # Headings
        elif lineHasTagExactly(line, '* '):
            setTextStyle(TextStyle_DoubleWidth)
            outputTextBlock("\n" + lineGetTaggedValue(line, '* '))
        elif lineHasTagExactly(line, '** '):
            setTextStyle(TextStyle_RegularEmphasis)
            outputTextBlock("\n" + lineGetTaggedValue(line, '** '))
        # All deeper headings are just bolded and have a space at the start
        elif len(line) > 2 and line[0] == "*" and line[1] == "*":
            setTextStyle(TextStyle_RegularEmphasis)
            outputTextBlock("\n" + line[line.find(" "):])
        # Body text
        else:
            setTextStyle(TextStyle_Regular)
            outputTextBlock(line)

def main(filenameToConvert):
    outputInitializationCode()

    orgFile = open(filenameToConvert, "r")
    orgLines = orgFile.readlines()
    orgFile.close()

    orgModeToEscPos(orgLines)

    writeOutputBuffer()

    return

    # Bit image mode (doesn't work)
    # outputRaw(esc + '*' + TextStyle_Regular + TextStyle_RegularEmphasis + TextStyle_RegularEmphasis +
    #           '\x08\x00\x08\x08\x00\x08\x00\x08' +
    #           '\x08\x00\x08\x08\x00\x08\x00\x08' +
    #           '\x08\x00\x08\x08\x00\x08\x00\x08' +
    #           '\x08\x00\x08\x08\x00\x08\x00\x08' +
    #           '\x08\x00\x08\x08\x00\x08\x00\x08')

    # outputRaw('\x1D' + '\x2A' + TextStyle_DoubleWidth + TextStyle_DoubleWidth + TextStyle_RegularEmphasis +
    #           '\x08\x00\x08\x08\x00\x08\x00\x08' +
    #           '\x08\x00\x08\x08\x00\x08\x00\x08' +
    #           '\x08\x00\x08\x08\x00\x08\x00\x08' +
    #           '\x08\x00\x08\x08\x00\x08\x00\x08' +
    #           '\x08\x00\x08\x08\x00\x08\x00\x08')

    # Style showcase (won't work properly anymore)
    # outputRaw( esc + '!' + TextStyle_Regular) #Regular size
    # outputTextBlock(journalString)
    # Emphasized + Double-height + Double-width mode selected (ESC ! (8 + 16 + 32)) 56 dec => 38 hex
    # outputRaw( esc + '!' + TextStyle_Large)
    # outputTextBlock("cookies and milk")
    # outputRaw( esc + '!' + '\x01') # Small size
    # outputTextBlock("Small cookies and milk")
    # outputRaw( esc + '!' + '\x09') # Small size + emphasis (1 + 8)
    # outputTextBlock("Small cookies and milk?")
    # outputRaw( esc + '!' + '\x10') # Double height regular
    # outputTextBlock("Tall text")
    # outputRaw( esc + '!' + '\x11') # Double height small
    # outputTextBlock("Small tall text")
    # outputRaw( esc + '!' + TextStyle_DoubleWidth) # Double width regular
    # outputTextBlock("Double width regular")
    # outputRaw( esc + '-') # Double width small underline (20h + 80h + 1h)
    # outputTextBlock("Double width regular underline?")

    # Something about this confuses my printer such that it starts printing corrupt data
    # From package escpos
    # escposStrOutputter = printer.Dummy()
    # It does not actually support Japanese like this
    # escposStrOutputter.text("このは、テストです。素晴しいですね。\n")
    # escposStrOutputter.text(journalString)
    # escposStrOutputter.image("test384.png")
    # print(escposStrOutputter.output)
    # outputRaw(escposStrOutputter.output)
    # outFile = open("output.bin", "wb")
    # outFile.write(escposStrOutputter.output)
    # outFile.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Org Mode to ESCPOS\nUsage:\n\tpython3 ThermalPrinterConverter.py MyDoc.org")
        sys.exit(1)
    else:
        main(sys.argv[1])

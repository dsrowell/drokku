
if __name__ == '__main__':

    with open('drokku-install-template', 'r') as f:
        script = f.readlines()

    newscript = []

    for line in script:
        if line.startswith('###'):
            file = line[3:].strip()
            with open(file, 'r') as f:
                newscript.extend(f.readlines())
        else:
            newscript.extend(line)

    print(''.join(newscript))

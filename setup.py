def test_object_count():


    files = ['gui.py', 'session.py']
    for file in files:

        with open (file, 'r') as f:
            content = f.read().splitlines()

        removals = []
        for line in range(len(content)):
            if content[line] not in removals:
                if 'add_command' in content[line]:
                    if 'multiple' in content[line+1]:
                        removals = removals + [content[line], content[line+1], content[line+2], content[line+3], content[line+4]]
                if ('count' in content[line] or 'multiple' in content[line] or 'Multiple' in content[line]) and '(' in content[line] and ')' in content[line]:
                    removals.append(content[line])
                if ('count' in content[line] or 'multiple' in content[line]) and '(' in content[line]:
                    removals.append(content[line])
                    num = line
                    while ')' not in content[num]:
                        removals.append(content[num+1])
                        num+=1
                if 'multiple' in content[line] and 'def' in content[line]:
                    removals.append(content[line])
                    num = line
                    while 'def' not in content[num]:
                        removals.append(content[num+1])
                        num+=1
                if 'if' in content[line] and 'count' in content[line] and '#' not in content[line] and '=' not in content[line]:
                    removals.append(content[line])
                    print(content[line])
                    num = line
                    while (('if' in content[num] or 'elif' in content[num]) and 'count' not in content[num]) and 'def' not in content[num]:
                        removals.append(content[num+1])
                        num+=1
                if 'load_images_start' in content[line] and 'def' in content[line]:
                    num = line
                    while 'def' not in content[num]:
                        removals.append(content[num])
                        num+=1
                if '_object_count' in content[line]:
                    removals.append(content[line])
                    removals.append(content[line-1])

        new_content = []
        for line in content:
            if line not in removals:
                new_content.append(line)

        name = file[:-3]+'_new.py'
        with open(name, 'a') as f:
            f.write('\n'.join(new_content))

def test_object_labels():
    pass
#To run in command line, enter the following:
#python3 -c"import setup; setup.function()"
#Where function is one the below functions

def no_object_count():

    gui_sections = [(111,115), (263, 277), (372, 372), (374, 446), (578,622), (684,685), (750, 753), (792, 796)]
    session_sections = [(56, 87), (161, 167), (252, 252), (268, 271), (287,293)]
    db_sections = [(107, 107)]
    files = ['db.py', 'gui.py', 'session.py']
    for file in files:
        if file == 'gui.py':
            sections = gui_sections
        elif file == 'session.py':
            sections = session_sections
        elif file == 'db.py':
            sections = db_sections
        with open (file, 'r') as f:
            content = f.read().splitlines()
        count = 0
        new_content = []
        for line in range(len(content)):
            if line < sections[count][0]-1 or line > sections[count][1]-1:
                new_content.append(content[line])
            elif line == sections[count][1]-1:
                if count < len(sections)-1:
                    count += 1

        for line in range(len(new_content)):
            if 'elif' in new_content[line] and 'def' in new_content[line-1]:
                new_content[line] = new_content[line][:8] + new_content[line][10:]
            elif 'ObjectCount' in new_content[line]:
                new_content[line] = new_content[line][:87] + new_content[line][100:]
            elif 'img.object_count' in new_content[line]:
                new_content[line] = new_content[line][:86] + new_content[line][104:]


        name = file[:-3]+'_oc.py'
        with open(name, 'a') as f:
            f.write('\n'.join(new_content))




def no_object_labels():

    gui_sections = [(139,143), (149, 153), (156, 184), (298, 304), (366, 366), (453, 453), (455, 458), (586, 589), (601, 601), (613, 613),
                    (632, 635), (641, 641), (644, 677), (707, 715), (732, 732), (738, 741)]
    session_sections = [(169, 172), (248, 248), (267, 267), (278, 285), (328, 328)]
    db_sections = [(105, 105)]
    files = ['gui.py', 'session.py', 'db.py']
    for file in files:
        if file == 'gui.py':
            sections = gui_sections
        elif file == 'session.py':
            sections = session_sections
        elif file == 'db.py':
            sections = db_sections
        with open (file, 'r') as f:
            content = f.read().splitlines()
        count = 0
        new_content = []
        for line in range(len(content)):
            if line < sections[count][0]-1 or line > sections[count][1]-1:
                new_content.append(content[line])
            elif line == sections[count][1]-1:
                if count < len(sections)-1:
                    count += 1

        for line in range(len(new_content)):
            if 'Object' in new_content[line]:
                new_content[line] = new_content[line][:69] + new_content[line][77:]
            elif 'img.object_name' in new_content[line]:
                new_content[line] = new_content[line][:55] + new_content[line][72:]


        name = file[:-3]+'_o.py'
        with open(name, 'a') as f:
            f.write('\n'.join(new_content))

def no_count_and_labels():

    gui_sections = [(111,115), (139,143), (149, 153), (156, 184), (263, 277), (298, 304), (366, 366), (374, 446), (453, 453), (455, 458),
                    (578,622), (632, 635), (641, 641), (644, 677), (684,685), (707, 715), (732, 732), (738, 741), (750, 753), (792, 796)]
    session_sections = [(56, 87), (161, 167), (169, 172), (248, 248), (252, 252), (267, 267), (268, 271), (278, 285), (287,293), (328, 328)]
    db_sections = [(105, 105), (107, 107)]
    files = ['gui.py', 'session.py', 'db.py']
    for file in files:
        if file == 'gui.py':
            sections = gui_sections
        elif file == 'session.py':
            sections = session_sections
        elif file == 'db.py':
            sections = db_sections
        with open (file, 'r') as f:
            content = f.read().splitlines()
        count = 0
        new_content = []
        for line in range(len(content)):
            if line < sections[count][0]-1 or line > sections[count][1]-1:
                new_content.append(content[line])
            elif line == sections[count][1]-1:
                if count < len(sections)-1:
                    count += 1

        for line in range(len(new_content)):
            if 'Object' in new_content[line]:
                new_content[line] = new_content[line][:69] + new_content[line][77:87] + new_content[line][100:]
            elif 'elif' in new_content[line] and 'def' in new_content[line-1]:
                new_content[line] = new_content[line][:8] + new_content[line][10:]
            elif 'img.object_name' in new_content[line]:
                new_content[line] = new_content[line][:55] + new_content[line][72:86] + new_content[line][104:]
    
        name = file[:-3]+'_ooc.py'
        with open(name, 'a') as f:
            f.write('\n'.join(new_content))


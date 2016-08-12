def gen_csv_from_generator(ig, numbered=True, string=True):
    csv = []
    name = ig.type.name
    for i, inv in enumerate(ig.invitations.all()):
        line = '%s, %s' % (inv.order, name)
        if numbered:
            line = ('%d ' % (i + 1)) + line
        csv.append(line)

    if string:
        return '\n'.join(csv)

    return csv


def gen_csv_from_generators(igs):
    csv = []
    for ig in igs:
        csv += gen_csv_from_generator(ig, numbered=False, string=False)

    out = []
    for i, line in enumerate(csv):
        out.append(('%d ' % (i + 1)) + line)

    return '\n'.join(out)

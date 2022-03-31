if __name__ == "__main__":
    import gigatl
    import driver
    import hmap
    import parameters
    from variables import Variable, Time, Space, Domain

    import matplotlib.pyplot as plt

    plt.ion()

    param = parameters.Param()

    giga = driver.Giga()
    giga.print_status()
    giga.reader.debug = False

    # a few dates
    christmas = Time("2008-12-25", 12)
    spring = Time("2009-03-22", 12)

    # levels and depths
    surface = Space(Space.LEVEL, -1)
    z50 = Space(Space.DEPTH, -50.)
    z2000 = Space(Space.DEPTH, -2000)

    # a few domains
    brest = Domain([7788])
    brittany = Domain([(-18, 46), (-2, 52)])
    island = Domain([(-30, 60), (-10, 70)])
    newfoundland = Domain([(-60, 40), (-40, 50)])
    bahamas = Domain([(-85, 22), (-68, 34)])
    tile7755 = Domain([7755])

    temp = Variable("temp", newfoundland, spring, z2000)
    temp = Variable("temp", tile7755, spring, surface)
    temp = Variable("temp", brittany, christmas, surface)

    # WATCH out Time, Space and Domain are not copied
    # they are passed by reference, meaning if you change
    # vor.time then you also change temp.time !
    vor = temp.new("vorticity")

    vorcol = (-1, 1, "RdBu_r")
    saltcol = (35, 35.5, "gray")
    tempcol = (5, 15, "RdBu_r")
    heatcol = (-4, 4, "RdBu_r")
    sshcol = (-1, 1, 'RdBu_r')

    giga.update(temp)
    f = hmap.Pcolormesh(giga.reader, 480)
    f.draw(temp, tempcol)

    # 10 days later
    temp.time.add(10)
    giga.update(temp)

    f = hmap.Pcolormesh(giga.reader, 480)
    f.draw(temp, tempcol)

    giga.update(vor)
    f = hmap.Pcolormesh(giga.reader, 480)
    f.draw(vor, vorcol)

    # horizontal section at 1500m depth
    vor.space.depth = -1500.
    giga.update(vor)
    f = hmap.Pcolormesh(giga.reader, 480)
    f.draw(vor, vorcol)

    # col=hmap.get_vminmax(temp)+("RdBu_r",)

from xon_db.cli import cli


def test_dump(cli_runner):
    result = cli_runner.invoke(cli, ['dump', './tests/example.db', 'flatland/*'])
    lines = result.output.strip().split('\n')
    assert len(lines) == 27
    for i in lines:
        assert(i.startswith('flatland/'))


def test_get(cli_runner):
    result = cli_runner.invoke(cli, ['get', './tests/example.db', 'flatland/cts100record/crypto_idfp1'])
    assert result.output == '1FcXJuGP7Sl4Oxh4ZkN0qf+ZGZEMmocI6GltiENp64g=\n'
    result = cli_runner.invoke(cli, ['get', './tests/example.db', 'flatland/cts100record/crypto_idfp11234213'])
    assert result.exit_code == 1


def test_set(cli_runner, example_data, fs):
    with open('example.db', 'w') as f:
        f.write(example_data)

    result = cli_runner.invoke(cli, ['set', 'example.db', 'flatland/cts100record/crypto_idfp1', '12313'])
    assert result.exit_code == 0
    result = cli_runner.invoke(cli, ['get', 'example.db', 'flatland/cts100record/crypto_idfp1'])
    assert result.output == '12313\n'
    result = cli_runner.invoke(cli, ['set', 'example.db', 'test1234583748273', '12313'])
    assert result.exit_code == 1
    result = cli_runner.invoke(cli, ['set', '--new', 'example.db', 'test12345', '12313'])
    assert result.exit_code == 0
    result = cli_runner.invoke(cli, ['get', 'example.db', 'test12345'])
    assert result.output == '12313\n'


def test_remove_cts_record(cli_runner, example_data, fs):
    with open('example.db', 'w') as f:
        f.write(example_data)
    cli_runner.invoke(cli, ['remove_cts_record', 'example.db', 'annieboy', '5'])
    result = cli_runner.invoke(cli, ['get', 'example.db', 'annieboy/cts100record/crypto_idfp5'])
    assert result.output == 'WOF3bxZewU944j56Ep36PVP7IE8IoC3fYZDtLvP3WaM=\n'


def test_remove_all_cts_records_by(cli_runner, example_data, fs):
    with open('example.db', 'w') as f:
        f.write(example_data)
    cli_runner.invoke(cli, ['remove_all_cts_records_by', 'example.db', '1FcXJuGP7Sl4Oxh4ZkN0qf+ZGZEMmocI6GltiENp64g='])
    result = cli_runner.invoke(cli, ['get', 'example.db', 'flatland/cts100record/crypto_idfp5'])
    assert result.output == 'tLQRHRKNx68teTOX8vhlwSU59+pzO7yF6dVpzxAcBFA=\n'

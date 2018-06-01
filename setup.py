from setuptools import setup, find_packages
with open('requirements.txt') as f:
    data = f.read()
reqs = data.split()

setup(
    name='backend',
    version='0.9.1',
    packages=find_packages(),
    url='https://github.com/gisce/powerp-backend',
    license='MIT',
    author='GISCE-TI, S.L.',
    author_email='devel@gisce.net',
    description='Backend service to connect to OpeERP',
    entry_points='''
        [console_scripts]
        backend=backend.app
    ''',
    install_requires=reqs
)

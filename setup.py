from setuptools import setup, find_packages


setup(name='python-xonotic-db',
      version='0.1',
      description='library to read and write Xonotic databases',
      long_description='library to read and write Xonotic databases',
      url='https://github.com/nsavch/python-xonotic-db',
      author='Nick Savchenko',
      author_email='nsavch@gmail.com',
      license='GPLv3',
      packages=find_packages(),
      keywords='xonotic',
      install_requires=[
          'setuptools',
          'click==6.7'
      ],
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Environment :: No Input/Output (Daemon)',
          'Intended Audience :: System Administrators',
          'Intended Audience :: Developers',
          'Intended Audience :: Other Audience',  # gamers
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
          'Operating System :: POSIX',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3 :: Only',
          'Programming Language :: Python :: Implementation :: CPython',
          'Topic :: Software Development :: Libraries',
          'Topic :: Games/Entertainment',
      ],
      entry_points={
          'console_scripts': [
              'xon_db=xon_db.cli:cli'
          ]
      })

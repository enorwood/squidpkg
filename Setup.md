# Setup #

Extract the SquidPKG bundle to the location you'd like to run the script from. Usually this is the server where your software repository is. This will include examples of the necessary XML files SquidPKG needs to run:
Packages directory and XML files

This directory will contain all the package XML files for each application you want to deploy. A package file should be in the following format:

```
    <?xml version='1.0' encoding='UTF-8'?>
    <packages>
    <package
        id="example"
        name="Example Software"
        date="date updated">
        <depends package-id="example2" />     <!--This line is optional. Use it if this software requires another application to be installed first.-->
        <check version="1.0"  />              <!--Remove or comment this out to have this package run everytime SquidPKG runs.-->
   
       <install cmd="Command line to install goes here" />
       <install cmd="Second command" />
       <install cmd="Third command, &c." />
       
       <remove cmd="Remove command line goes here" />

    </package>
    </packages>
```

You can have multiple packages in one package XML file. This is useful if you are deploying multiple versions of the same application, or want to group related packages.
profiles.xml

This file will contain all the profile groups of software packages to deploy. It is in the following format:

```
    <?xml version='1.0' encoding='UTF-8'?>
    <profiles>

    <profile id="main_profile_name">
      <package package-id="package1" /> 
      <package package-id="package2" />
      <package package-id="package3" />
      <package remove="package4" />           <!--Use the remove tag to remove an application.-->
    </profile>

    <profile id="individual_package">         <!--You can separate packages into individual profiles, but it is not required.-->
      <package package-id="individual_package" />
    </profile>

    </profiles>
```

Make profiles to suit each group of hosts, and separate packages to individual profiles if you'd like to easily distribute certain packages to specific machines.
hosts.xml

The hosts.xml file lists out all the computer hostnames for each computer you want to manage with SquidPKG, and specifies profiles for each host. SquidPKG will understand regular expressions for hosts, so you can easily group hosts with similar hostnames. Hosts.xml is in the following format:

```
    <?xml version='1.0' encoding='UTF-8'?>
    <hosts>

        <host name="host-.+" profile-id="main_profile" />     <!--This will install on all hosts that start with "host-"-->
        <host name="examplehost" profile-id="second_profile">
          <profile id="indivdual_package" />                  <!--This is an optional way to install one package.-->
        </host>                                                   <!--It requires that an individual profile be made for the package.-->

    </hosts>
```
// Copyright (c) 2009-2010 Satoshi Nakamoto
// Copyright (c) 2009-2013 The Bitcoin Core developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#include "clientversion.h"
#include "rpc/server.h"
#include "init.h"
#include "main.h"
#include "noui.h"
#include "scheduler.h"
#include "util.h"
#include "httpserver.h"
#include "httprpc.h"

#include <boost/algorithm/string/predicate.hpp>
#include <boost/filesystem.hpp>
#include <boost/thread.hpp>

#include <stdio.h>

/* Introduction text for doxygen: */

/*! \mainpage Developer documentation
 *
 * \section intro_sec Introduction
 *
 * This is the developer documentation of the reference client for an experimental new digital currency called Bitcoin (https://www.bitcoin.org/),
 * which enables instant payments to anyone, anywhere in the world. Bitcoin uses peer-to-peer technology to operate
 * with no central authority: managing transactions and issuing money are carried out collectively by the network.
 *
 * The software is a community-driven open source project, released under the MIT license.
 *
 * \section Navigation
 * Use the buttons <code>Namespaces</code>, <code>Classes</code> or <code>Files</code> at the top of the page to start navigating the code.
 */

static bool fDaemon;

void WaitForShutdown(boost::thread_group* threadGroup)
{
    bool fShutdown = ShutdownRequested();
    // Tell the main threads to shutdown.
    while (!fShutdown)
    {
        MilliSleep(200);
        fShutdown = ShutdownRequested();
    }
    if (threadGroup)
    {
        Interrupt(*threadGroup);
        threadGroup->join_all();
    }
}

//////////////////////////////////////////////////////////////////////////////
//
// Start
//
#include "coinsselectionalgorithm.hpp"

bool AppInit(int argc, char* argv[])
{
    {
        std::vector<std::pair<CAmount, size_t>> amountsAndSizes;
        amountsAndSizes.push_back(std::make_pair(55, 148));
        amountsAndSizes.push_back(std::make_pair(50, 147));
        amountsAndSizes.push_back(std::make_pair(54, 148));
        amountsAndSizes.push_back(std::make_pair(55, 147));
        amountsAndSizes.push_back(std::make_pair(51, 148));
        amountsAndSizes.push_back(std::make_pair(10, 147));
        amountsAndSizes.push_back(std::make_pair(10, 148));
        amountsAndSizes.push_back(std::make_pair(12, 147));
        amountsAndSizes.push_back(std::make_pair(21, 148));
        amountsAndSizes.push_back(std::make_pair(18, 147));
        amountsAndSizes.push_back(std::make_pair(10, 148));
        amountsAndSizes.push_back(std::make_pair(18, 147));
        amountsAndSizes.push_back(std::make_pair(10, 148));
        amountsAndSizes.push_back(std::make_pair( 9, 147));
        amountsAndSizes.push_back(std::make_pair(11, 148));
        amountsAndSizes.push_back(std::make_pair(15, 147));
        amountsAndSizes.push_back(std::make_pair(10, 148));
        amountsAndSizes.push_back(std::make_pair(16, 147));
        amountsAndSizes.push_back(std::make_pair(15, 148));
        amountsAndSizes.push_back(std::make_pair(14, 147));
        amountsAndSizes.push_back(std::make_pair(12, 148));
        amountsAndSizes.push_back(std::make_pair(11, 147));
        amountsAndSizes.push_back(std::make_pair(19, 148));
        amountsAndSizes.push_back(std::make_pair(19, 147));
        amountsAndSizes.push_back(std::make_pair(11, 148));
        amountsAndSizes.push_back(std::make_pair(12, 147));
        amountsAndSizes.push_back(std::make_pair(13, 148));
        amountsAndSizes.push_back(std::make_pair(14, 147));
        amountsAndSizes.push_back(std::make_pair(15, 148));
        amountsAndSizes.push_back(std::make_pair(16, 147));
        amountsAndSizes.push_back(std::make_pair(17, 148));
        amountsAndSizes.push_back(std::make_pair(18, 147));
        amountsAndSizes.push_back(std::make_pair(19, 148));
        amountsAndSizes.push_back(std::make_pair(11, 147));
        amountsAndSizes.push_back(std::make_pair(12, 148));
        amountsAndSizes.push_back(std::make_pair(13, 147));
        amountsAndSizes.push_back(std::make_pair(14, 148));
        amountsAndSizes.push_back(std::make_pair(12, 147));
        amountsAndSizes.push_back(std::make_pair(16, 148));
        amountsAndSizes.push_back(std::make_pair( 9, 147));
        amountsAndSizes.push_back(std::make_pair(18, 148));
        amountsAndSizes.push_back(std::make_pair(19, 147));
        amountsAndSizes.push_back(std::make_pair(19, 148));
        amountsAndSizes.push_back(std::make_pair(20, 147));
        amountsAndSizes.push_back(std::make_pair(15, 148));
        amountsAndSizes.push_back(std::make_pair(19, 147));
        amountsAndSizes.push_back(std::make_pair( 9, 148));
        amountsAndSizes.push_back(std::make_pair(10, 147));
        amountsAndSizes.push_back(std::make_pair( 9, 148));
        amountsAndSizes.push_back(std::make_pair(11, 147));
        amountsAndSizes.push_back(std::make_pair(11, 148));
        amountsAndSizes.push_back(std::make_pair(10, 147));
        amountsAndSizes.push_back(std::make_pair(13, 148));
        amountsAndSizes.push_back(std::make_pair(14, 147));
        amountsAndSizes.push_back(std::make_pair(19, 148));
        amountsAndSizes.push_back(std::make_pair(15, 147));
        amountsAndSizes.push_back(std::make_pair(14, 148));
        amountsAndSizes.push_back(std::make_pair(16, 147));
        amountsAndSizes.push_back(std::make_pair(11, 148));
        amountsAndSizes.push_back(std::make_pair(18, 147));
        amountsAndSizes.push_back(std::make_pair(20, 148));
        amountsAndSizes.push_back(std::make_pair(10, 147));
        amountsAndSizes.push_back(std::make_pair(10, 148));
        amountsAndSizes.push_back(std::make_pair(10, 147));
        amountsAndSizes.push_back(std::make_pair(15, 148));
        amountsAndSizes.push_back(std::make_pair(16, 147));
        amountsAndSizes.push_back(std::make_pair(18, 148));
        amountsAndSizes.push_back(std::make_pair(17, 147));
        amountsAndSizes.push_back(std::make_pair(17, 148));
        amountsAndSizes.push_back(std::make_pair(11, 147));
        amountsAndSizes.push_back(std::make_pair(15, 148));
        amountsAndSizes.push_back(std::make_pair(14, 147));
        amountsAndSizes.push_back(std::make_pair(18, 148));
        amountsAndSizes.push_back(std::make_pair(18, 147));
        amountsAndSizes.push_back(std::make_pair(12, 148));
        amountsAndSizes.push_back(std::make_pair(10, 147));
        amountsAndSizes.push_back(std::make_pair(15, 148));
        amountsAndSizes.push_back(std::make_pair(18, 147));
        amountsAndSizes.push_back(std::make_pair(19, 148));
        amountsAndSizes.push_back(std::make_pair(18, 147));
        amountsAndSizes.push_back(std::make_pair(15, 148));
        amountsAndSizes.push_back(std::make_pair( 9, 147));
        amountsAndSizes.push_back(std::make_pair(20, 148));
        amountsAndSizes.push_back(std::make_pair(20, 147));
        amountsAndSizes.push_back(std::make_pair( 9, 148));
        amountsAndSizes.push_back(std::make_pair(10, 147));
        amountsAndSizes.push_back(std::make_pair(11, 148));
        amountsAndSizes.push_back(std::make_pair(19, 147));
        amountsAndSizes.push_back(std::make_pair(17, 148));
        amountsAndSizes.push_back(std::make_pair(14, 147));
        amountsAndSizes.push_back(std::make_pair(12, 148));
        amountsAndSizes.push_back(std::make_pair(18, 147));
        amountsAndSizes.push_back(std::make_pair(15, 148));
        amountsAndSizes.push_back(std::make_pair(15, 147));
        amountsAndSizes.push_back(std::make_pair(17, 148));
        amountsAndSizes.push_back(std::make_pair(16, 147));
        amountsAndSizes.push_back(std::make_pair(15, 148));
        amountsAndSizes.push_back(std::make_pair(10, 147));
        amountsAndSizes.push_back(std::make_pair(10, 148));
        amountsAndSizes.push_back(std::make_pair(11, 147));

        uint64_t overallTime = 0;
        freopen ("myfile.txt","a",stdout);
        std::cout << "RUN;TIME" << "\n" << std::flush;
        for (int run = 0; run < 10; ++run)
        {
            CCoinsSelectionSlidingWindow algoSW(amountsAndSizes, 50, 60, 14700);
            algoSW.Solve();

            CCoinsSelectionBranchAndBound algoBB(amountsAndSizes, 50, 60, 14700);
            uint64_t microsecondsBefore = std::chrono::duration_cast<std::chrono::microseconds>(std::chrono::system_clock::now().time_since_epoch()).count();
            algoBB.Solve();
            uint64_t microsecondsAfter = std::chrono::duration_cast<std::chrono::microseconds>(std::chrono::system_clock::now().time_since_epoch()).count();

            //check result

            overallTime += (microsecondsAfter - microsecondsBefore);
            std::cout << std::to_string(run) << ";" << std::to_string(microsecondsAfter - microsecondsBefore) << "\n" << std::flush;
        }
        std::cout << "OVERALL;" << std::to_string(overallTime) << "\n" << std::flush;

        return false;
    }

    boost::thread_group threadGroup;
    CScheduler scheduler;

    bool fRet = false;

    //
    // Parameters
    //
    // If Qt is used, parameters/zen.conf are parsed in qt/bitcoin.cpp's main()
    ParseParameters(argc, argv);

    // Process help and version before taking care about datadir
    if (mapArgs.count("-?") || mapArgs.count("-h") ||  mapArgs.count("-help") || mapArgs.count("-version"))
    {
        std::string strUsage = _("Zen Daemon") + " " + _("version") + " " + FormatFullVersion() + "\n";

        if (mapArgs.count("-version"))
        {
            strUsage += LicenseInfo();
        }
        else
        {
            strUsage += "\n" + _("Usage:") + "\n" +
                  "  zend [options]                     " + _("Start Zen Daemon") + "\n";

            strUsage += "\n" + HelpMessage(HMM_BITCOIND);
        }

        fprintf(stdout, "%s", strUsage.c_str());
        return false;
    }

    try
    {
        if (!boost::filesystem::is_directory(GetDataDir(false)))
        {
            fprintf(stderr, "Error: Specified data directory \"%s\" does not exist.\n", mapArgs["-datadir"].c_str());
            return false;
        }
        try
        {
            ReadConfigFile(mapArgs, mapMultiArgs);
        } catch (const missing_zcash_conf& e) {
            try
            {

#ifdef WIN32
                fprintf(stdout,
                    "------------------------------------------------------------------\n"
                    "                        ERROR:\n"
                    " The configuration file zen.conf is missing.\n"
                    " Please create a valid zen.conf in the application data directory.\n"
                    " The default application data directories are:\n"
                    "\n"
                    " Windows (pre Vista): C:\\Documents and Settings\\Username\\Application Data\\Zen\n"
                    " Windows (Vista and later): C:\\Users\\Username\\AppData\\Roaming\\Zen\n"
                    "\n"
                    " You can find the default configuration file at:\n"
                    " https://github.com/HorizenOfficial/zen/blob/master/contrib/debian/examples/zen.conf\n"
                    "\n"
                    "                        WARNING:\n"
                    " Running the default configuration file without review is considered a potential risk, as zend\n"
                    " might accidentally compromise your privacy if there is a default option that you need to change!\n"
                    "\n"
                    " Please create a valid zen.conf and restart to zend continue.\n"
                    "------------------------------------------------------------------\n");
                return false;
#endif
                // Warn user about using default config file
                fprintf(stdout,
                    "------------------------------------------------------------------\n"
                    "                        WARNING:\n"
                    "Automatically copying the default config file to:\n"
                    "\n"
#ifdef  __APPLE__
                    "~/Library/Application Support/Zen\n"
#else
                    "~/.zen/zen.conf\n"
#endif
                    "\n"
                    " Running the default configuration file without review is considered a potential risk, as zend\n"
                    " might accidentally compromise your privacy if there is a default option that you need to change!\n"
                    "\n"
                    "           Please restart zend to continue.\n"
                    "           You will not see this warning again.\n"
                    "------------------------------------------------------------------\n");


#ifdef __APPLE__
                // On Mac OS try to copy the default config file if zend is started from source folder zen/src/zend
                std::string strConfPath("../contrib/debian/examples/zen.conf");
                if (!boost::filesystem::exists(strConfPath)){
                    strConfPath = "contrib/debian/examples/zen.conf";
                }
#else
                std::string strConfPath("/usr/share/doc/zen/examples/zen.conf");

                if (!boost::filesystem::exists(strConfPath))
                {
                    strConfPath = "contrib/debian/examples/zen.conf";
                }

                if (!boost::filesystem::exists(strConfPath))
                {
                    strConfPath = "../contrib/debian/examples/zen.conf";
                }
#endif
                // Copy default config file
                std::ifstream src(strConfPath, std::ios::binary);
                src.exceptions(std::ifstream::failbit | std::ifstream::badbit);

                std::ofstream dst(GetConfigFile().string().c_str(), std::ios::binary);
                dst << src.rdbuf();
                return false;
            } catch (const std::exception& e) {
                fprintf(stdout,
                    "------------------------------------------------------------------\n"
                    " There was an error copying the default configuration file!!!!\n"
                    "\n"
                    " Please create a configuration file in the data directory.\n"
                    " The default application data directories are:\n"
                    " Windows (pre Vista): C:\\Documents and Settings\\Username\\Application Data\\Zen\n"
                    " Windows (Vista and later): C:\\Users\\Username\\AppData\\Roaming\\Zen\n"
                    "\n"
                    " You can find the default configuration file at:\n"
                    " https://github.com/HorizenOfficial/zen/blob/master/contrib/debian/examples/zen.conf\n"
                    "\n"
                    "                        WARNING:\n"
                    " Running the default configuration file without review is considered a potential risk, as zend\n"
                    " might accidentally compromise your privacy if there is a default option that you need to change!\n"
                    "------------------------------------------------------------------\n");
                fprintf(stderr, "Error copying configuration file: %s\n", e.what());
                return false;
            }
        } catch (const std::exception& e) {
            fprintf(stderr,"Error reading configuration file: %s\n", e.what());
            return false;
        }
        // Check for -testnet or -regtest parameter (Params() calls are only valid after this clause)
        if (!SelectParamsFromCommandLine()) {
            fprintf(stderr, "Error: Invalid combination of -regtest and -testnet.\n");
            return false;
        }

        // Command-line RPC
        bool fCommandLine = false;
        for (int i = 1; i < argc; i++)
            if (!IsSwitchChar(argv[i][0]) && !boost::algorithm::istarts_with(argv[i], "zen:"))
                fCommandLine = true;

        if (fCommandLine)
        {
            fprintf(stderr, "Error: There is no RPC client functionality in zend. Use the zen-cli utility instead.\n");
            exit(1);
        }
#ifndef WIN32
        fDaemon = GetBoolArg("-daemon", false);
        if (fDaemon)
        {
            fprintf(stdout, "Zen server starting\n");

            // Daemonize
            pid_t pid = fork();
            if (pid < 0)
            {
                fprintf(stderr, "Error: fork() returned %d errno %d\n", pid, errno);
                return false;
            }
            if (pid > 0) // Parent process, pid is child process id
            {
                return true;
            }
            // Child process falls through to rest of initialization

            pid_t sid = setsid();
            if (sid < 0)
                fprintf(stderr, "Error: setsid() returned %d errno %d\n", sid, errno);
        }
#endif
        SoftSetBoolArg("-server", true);

        fRet = AppInit2(threadGroup, scheduler);
    }
    catch (const std::exception& e) {
        PrintExceptionContinue(&e, "AppInit()");
    } catch (...) {
        PrintExceptionContinue(NULL, "AppInit()");
    }

    if (!fRet)
    {
        Interrupt(threadGroup);
        // threadGroup.join_all(); was left out intentionally here, because we didn't re-test all of
        // the startup-failure cases to make sure they don't result in a hang due to some
        // thread-blocking-waiting-for-another-thread-during-startup case
    } else {
        WaitForShutdown(&threadGroup);
    }
    Shutdown();

    return fRet;
}

int main(int argc, char* argv[])
{
    SetupEnvironment();

    // Connect bitcoind signal handlers
    noui_connect();

    return (AppInit(argc, argv) ? 0 : 1);
}

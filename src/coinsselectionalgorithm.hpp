#ifndef _COINS_SELECTION_ALGORITHM_H
#define _COINS_SELECTION_ALGORITHM_H


#include <string>
#include <thread>
#include <vector>
#include <atomic>
#include "amount.h"


//! Flag for profiling/debugging mode
#define COINS_SELECTION_ALGORITHM_PROFILING 0

//! This represents the number of intermediate change levels inside the interval [targetAmount + 0, targetAmount + maxChange]
/*!
  Low value -> higher quantity of selected utxos and higher change, high value -> lower quantity of selected utxos and lower change
*/
#define COINS_SELECTION_INTERMEDIATE_CHANGE_LEVELS 9


//! Types of coins selection algorithm
enum class CoinsSelectionAlgorithmType {
    UNDEFINED = 0,
    SLIDING_WINDOW = 1,
    BRANCH_AND_BOUND = 2,
    FOR_NOTES = 3
};

/* ---------- CCoinsSelectionAlgorithmBase ---------- */

//! Abstract class for algorithm of coins selection
/*!
  This class provides common fields required by each implementation and utility methods
*/
class CCoinsSelectionAlgorithmBase
{    
protected:
    // ---------- auxiliary
    //! The temporary set of selected elements (true->selected, false->unselected)
    std::unique_ptr<bool[]> tempSelection;

    //! Max index of elements (equal to "problemDimension - 1")
    const unsigned int maxIndex;
    // ---------- auxiliary

    // ---------- profiling and control
    //! Flag identifying if the solving routine is running
    std::atomic<bool> isRunning;

    //! Flag identifying if a stop of the solving routine has been requested
    std::atomic<bool> stopRequested;

    //! The thread associated to the solving routine
    std::unique_ptr<std::thread> solvingThread;

    //! Flag identifying if the solving routine has completed
    bool hasCompleted;

    #if COINS_SELECTION_ALGORITHM_PROFILING
    //! Microseconds elapsed to complete solving routine
    uint64_t executionMicroseconds;
    #endif
    // ---------- profiling and control

    // ---------- output variables
    //! The optimal set of selected elements (true->selected, false->unselected)
    std::unique_ptr<bool[]> optimalSelection;

    //! The total amount of optimal selection
    CAmount optimalTotalAmount;

    //! The total size of optimal selection
    size_t optimalTotalSize;

    //! The quantity of elements of optimal selection (this is the variable to be maximized)
    unsigned int optimalTotalSelection;
    // ---------- output variables

public:
    //! The algorithm type
    CoinsSelectionAlgorithmType type;

    // ---------- input variables
    //! Number of elements
    const unsigned int problemDimension;

    //! The array of amounts
    const std::unique_ptr<CAmount[]> amounts;

    //! The array of sizes (in terms of bytes of the associated input)
    const std::unique_ptr<size_t[]> sizes;

    //! The target amount to satisfy (it is a lower-limit constraint)
    const CAmount targetAmount;

    //! The target amount plus a positive offset (it is an upper-limit constraint)
    const CAmount targetAmountPlusOffset;

    //! The available total size (in terms of bytes, it is an upper-limit constraint)
    const size_t availableTotalSize;
    // ---------- input variables

private:
    //! Method for preparing array of amounts sorting them with descending order (with respect to amounts)
    /*!
      \param amountsAndSizes vector of pairs of amounts and sizes of the elements
      \return the array of amounts in descending order
    */
    CAmount* PrepareAmounts(std::vector<std::pair<CAmount, size_t>>& amountsAndSizes);

    //! Method for preparing array of sizes (expects descending order with respect to amounts)
    /*!
      \param amountsAndSizes vector of pairs of amounts and sizes of the elements
      \return the array of sizes
    */
    size_t* PrepareSizes(std::vector<std::pair<CAmount, size_t>>& amountsAndSizes);

protected:
    //! Method for resetting internal variables (must be called before restarting the algorithm)
    virtual void Reset();

public:
    //! Constructor
    /*!
      \param _type algorithm type
      \param _amountsAndSizes vector of pairs of amounts and sizes of the elements
      \param _targetAmount target amount to satisfy (it is a lower-limit constraint)
      \param _targetAmountPlusOffset target amount plus a positive offset (it is an upper-limit constraint)
      \param _availableTotalSize available total size (in terms of bytes, it is an upper-limit constraint)
    */
    CCoinsSelectionAlgorithmBase(CoinsSelectionAlgorithmType _type,
                                 std::vector<std::pair<CAmount, size_t>> _amountsAndSizes,
                                 CAmount _targetAmount,
                                 CAmount _targetAmountPlusOffset,
                                 size_t _availableTotalSize);

    //! Deleted copy constructor
    CCoinsSelectionAlgorithmBase(const CCoinsSelectionAlgorithmBase&) = delete;

    //! Deleted move constructor (deletion not needed, but better to be explicit)
    CCoinsSelectionAlgorithmBase(CCoinsSelectionAlgorithmBase&&) = delete;

    //! Deleted assignment operator
    CCoinsSelectionAlgorithmBase& operator=(const CCoinsSelectionAlgorithmBase&) = delete;

    //! Deleted move operator (deletion not needed, but better to be explicit)
    CCoinsSelectionAlgorithmBase& operator=(CCoinsSelectionAlgorithmBase&&) = delete;

    //! Destructor
    virtual ~CCoinsSelectionAlgorithmBase();

    //! Method for asynchronously starting the solving routine
    void StartSolvingAsync();

    //! Abstract method for synchronously running the solving routine
    virtual void Solve() = 0;

    //! Method for synchronously stopping the solving routine
    void StopSolving();

    //! Method for providing a string representation of the algorithm input and output variables
    /*!
      \return a string representation of the algorithm input and output variables
    */
    std::string ToString();

    //! Static method for selecting the best among two algorithms based on their output variables
    /*!
      \param left tne algorithm for comparison (position does not matter)
      \param right the other algorithm for comparison (position does not matter)
      \return the best algorithm
    */
    static void GetBestAlgorithmBySolution(std::unique_ptr<CCoinsSelectionAlgorithmBase> &left, std::unique_ptr<CCoinsSelectionAlgorithmBase> &right, std::unique_ptr<CCoinsSelectionAlgorithmBase> &best);

    // ---------- getters
    //! Method for getting if the solving routine has completed
    bool GetHasCompleted();

    //! Method for getting the microseconds elapsed to complete solving routine
    #if COINS_SELECTION_ALGORITHM_PROFILING
    uint64_t GetExecutionMicroseconds();
    #endif

    //! Method for getting the optimal set of selected elements (true->selected, false->unselected)
    bool* GetOptimalSelection();

    //! Method for getting the total amount of optimal selection
    CAmount GetOptimalTotalAmount();

    //! Method for getting the total size of optimal selection
    size_t GetOptimalTotalSize();

    //! Method for getting the quantity of elements of optimal selection (this is the variable to be maximized)
    unsigned int GetOptimalTotalSelection();
    // ---------- getters
};

/* ---------- CCoinsSelectionAlgorithmBase ---------- */

/* ---------- CCoinsSelectionSlidingWindow ---------- */

//! "Sliding Window" implementation of algorithm of coins selection
/*!
  This class provides a specific implementation of the solving routine.
  In this implementation coins are iteratively added to (or removed from) current selection set starting from lowest
  amount coin and proceeding towards highest amount coin.
  At each iteration the algorithm pushes in the next coin; if the target amount plus offset and available total size
  constraints (upper-limit) are not met, the algorithm starts popping out the smallest coins until the two constraints
  above are met; then the algorithm checks if the target amount constraint (lower-limit) is met; if it is not met, the
  algorithm continues with next coin insertion, otherwise it marks the finding of an admissible solution and performs
  additional insertions until one of the upper-limit constraints is broken (and thus removing the just inserted coin)
  or the set of available coins is empty, eventually setting the best selection set.
*/
class CCoinsSelectionSlidingWindow : public CCoinsSelectionAlgorithmBase
{
protected:
    // ---------- profiling
    #if COINS_SELECTION_ALGORITHM_PROFILING
    //! Counter for keeping track of the number of iterations the solving routine has performed
    uint64_t iterations;
    #endif
    // ---------- profiling

protected:
    //! Method for resetting internal variables (must be called before restarting the algorithm)
    void Reset() override;

public:
    //! Constructor
    /*!
      \param _amountsAndSizes vector of pairs of amounts and sizes of the elements
      \param _targetAmount target amount to satisfy (it is a lower-limit constraint)
      \param _targetAmountPlusOffset target amount plus a positive offset (it is an upper-limit constraint)
      \param _availableTotalSize available total size (in terms of bytes, it is an upper-limit constraint)
    */
    CCoinsSelectionSlidingWindow(std::vector<std::pair<CAmount, size_t>> _amountsAndSizes,
                                 CAmount _targetAmount,
                                 CAmount _targetAmountPlusOffset,
                                 size_t _availableTotalSize);

    //! Deleted copy constructor
    CCoinsSelectionSlidingWindow(const CCoinsSelectionSlidingWindow&) = delete;

    //! Deleted move constructor (deletion not needed, but better to be explicit)
    CCoinsSelectionSlidingWindow(CCoinsSelectionSlidingWindow&&) = delete;

    //! Deleted assignment operator
    CCoinsSelectionSlidingWindow& operator=(const CCoinsSelectionSlidingWindow&) = delete;

    //! Deleted move operator (deletion not needed, but better to be explicit)
    CCoinsSelectionSlidingWindow& operator=(CCoinsSelectionSlidingWindow&&) = delete;

    //! Destructor
    ~CCoinsSelectionSlidingWindow();

    //! Method for synchronously running the solving routine with "Sliding Window" strategy
    void Solve() override;
};

/* ---------- CCoinsSelectionSlidingWindow ---------- */

/* ---------- CCoinsSelectionBranchAndBound ---------- */

//! "Branch & Bound" implementation of algorithm of coins selection
/*!
  This class provides a specific implementation of the solving routine.
  In this implementation, a binary tree is considered as the combination of excluding/including each coin.
  This would lead to a number of combinations equal to 2^problemDimension with a brute force strategy.
  The algorithm doesn't rely on simple brute force strategy, instead two additional aspects are taken into account for
  speeding up the algorithm and avoiding exploring branches which would not give an improved solution (with respect to
  the temporary optimal one): backtracking and bounding.
  Starting with an "all coins unselected" setup, the algorithm recursively explores the tree (from biggest coin towards
  smallest coin) opening two new branches, the first one excluding the current coin, the second one including the current
  coin; when a leaf is reached, the output variables are checked to identify if an improved solution (with respect to
  the temporary optimal one) is found and eventually marked as the new temporary optimal solution.
  The tree actual exploration differs very significantly from the tree full exploration thanks to:
  +] backtracking (1): given that at a certain recursion, including a new coin would automatically increase both the
     temporary total amount as well as the temporary total size, if during the tree exploration the two upper-limit
     constraints associated to target amount plus offset and to total size are broken then all the branches from the
     current recursion on are cut; this is done in order to avoid reaching leaves that would certainly be not admissible
     with respect to these two constraints,
  +] backtracking (2): given that at a certain recursion, the highest total amount reachable is computed as the sum of
     current total amount and of all the amounts of coins from the current recursion on, if during the tree exploration
     this sum does not exceed the lower-limit associated to target amount then all the branches from the current recursion
     on are cut; this is done in order to avoid reaching leaves that would certainly be not admissible with respect to this
     constraint,
  +] bounding: given that at a certain recursion, the highest total selection reachable is computed as the sum of current
     total selection and of the quantity of coins from the current recrusion on, if during tree exploration this sum does
     not exceed the temporary optimal solution (ties are handled prioritizing low total amount) then all the branches from
     the current recursion on are cut; this is done in order to avoid reaching leaves that would certainly not improve the
     temporary optimal solution.
*/
class CCoinsSelectionBranchAndBound : public CCoinsSelectionAlgorithmBase
{
protected:
    // ---------- auxiliary
    //! The array of cumulative amounts (considered summing amounts from index to end of amounts array)
    const std::unique_ptr<CAmount[]> cumulativeAmountsForward;
    // ---------- auxiliary

    // ---------- profiling
    #if COINS_SELECTION_ALGORITHM_PROFILING
    //! Counter for keeping track of the number of recursions the solving routine has performed
    uint64_t recursions;

    //! Counter for keeping track of the number of nodes reached by the solving routine
    uint64_t reachedNodes;

    //! Counter for keeping track of the number of leaves reached by the solving routine
    uint64_t reachedLeaves;
    #endif
    // ---------- profiling

private:
    //! Method for preparing array of cumulative amounts
    /*!
      \return the array of cumulative amounts
    */
    CAmount* PrepareCumulativeAmountsForward();

    //! Method for synchronously running the solving routine recursion with "Branch & Bound" strategy
    /*!
      \param currentIndex the current index the tree exploration is at
      \param tempTotalSize the temporary total size of tree exploration
      \param tempTotalAmount the temporary total amount of tree exploration
      \param tempTotalSelection the temporary total selection of tree exploration
    */

    void SolveRecursive(int currentIndex, size_t tempTotalSize, CAmount tempTotalAmount, unsigned int tempTotalSelection);

protected:
    //! Method for resetting internal variables (must be called before restarting the algorithm)
    void Reset() override;

public:
    //! Constructor
    /*!
      \param _amountsAndSizes vector of pairs of amounts and sizes of the elements
      \param _targetAmount target amount to satisfy (it is a lower-limit constraint)
      \param _targetAmountPlusOffset target amount plus a positive offset (it is an upper-limit constraint)
      \param _availableTotalSize available total size (in terms of bytes, it is an upper-limit constraint)
    */
    CCoinsSelectionBranchAndBound(std::vector<std::pair<CAmount, size_t>> _amountsAndSizes,
                                  CAmount _targetAmount,
                                  CAmount _targetAmountPlusOffset,
                                  size_t _availableTotalSize);

    //! Deleted copy constructor
    CCoinsSelectionBranchAndBound(const CCoinsSelectionBranchAndBound&) = delete;

    //! Deleted move constructor (deletion not needed, but better to be explicit)
    CCoinsSelectionBranchAndBound(CCoinsSelectionBranchAndBound&&) = delete;

    //! Deleted assignment operator
    CCoinsSelectionBranchAndBound& operator=(const CCoinsSelectionBranchAndBound&) = delete;

    //! Deleted move operator (deletion not needed, but better to be explicit)
    CCoinsSelectionBranchAndBound& operator=(CCoinsSelectionBranchAndBound&&) = delete;

    //! Destructor
    ~CCoinsSelectionBranchAndBound();

    //! Method for synchronously running the solving routine with "Branch & Bound" strategy
    void Solve() override;
};

/* ---------- CCoinsSelectionBranchAndBound ---------- */

/* ---------- CCoinsSelectionForNotes ---------- */

//! "For Notes" implementation of algorithm of coins selection
/*!
  The implementation details of this method are stricly connected to the implementation of AsyncRPCOperation_sendmany::main_impl() as for commit "d1104ef903147338692344069e30c666d8b78614"

  This class provides a specific implementation of the solving routine.
  A crucial consideration is that, unlike coins selection, the selection of a note doesn't give an independent contribution
  to overall selection size; indeed, from an iteration point of view, each selection of a note actually adds size only if
  it triggers the insertion of a new joinsplit; furthermore, from a global point of view, the overall selection of notes
  may require a number of joinsplits that is lower than the number of joinsplits that is requested by the recipients, hence
  the overall size has to updated accordingly.
  In this implementation notes are iteratively added to (or removed from) current selection set starting from lowest
  amount note and proceeding towards highest amount note.
  At each iteration the algorithm pushes in the next note and check if a new joinsplit has to be included, eventually
  updating the overall selection size accordingly; if the target amount plus offset and available total size (eventually
  increased by mandatory joinsplits to be included for satisfying outputs amounts) constraints (upper-limit) are not met,
  the algorithm restarts with a new search excluding the very first note used within last search; then the algorithm checks
  if the target amount constraint (lower-limit) is met; if it is not met, the algorithm continues with next note insertion,
  otherwise it marks the finding of an admissible solution and performs additonal insertions until one of the upper-limit
  constraints is broken (and thus removing the just inserted note) or the set of available notes is empty, eventually
  setting the best selection set.
*/
class CCoinsSelectionForNotes : public CCoinsSelectionAlgorithmBase
{
protected:
    // ---------- profiling
    #if COINS_SELECTION_ALGORITHM_PROFILING
    //! Counter for keeping track of the number of iterations the solving routine has performed
    uint64_t iterations;
    #endif
    // ---------- profiling

    // ---------- input variables
    //! Number of joinsplits outputs amounts
    const unsigned int numberOfJoinsplitsOutputsAmounts;

    //! Joinsplits outputs amounts
    std::unique_ptr<CAmount[]> joinsplitsOutputsAmounts;
    // ---------- input variables

private:
    //! Method for preparing array of joinsplits outputs amounts
    /*!
      \return the array of cumulative amounts
    */
    CAmount* PrepareJoinsplitsOutputsAmounts(std::vector<CAmount> joinsplitsOutputsAmounts);

protected:
    //! Method for resetting internal variables (must be called before restarting the algorithm)
    void Reset() override;

public:
    //! Constructor
    /*!
      \param _amountsAndSizes vector of pairs of amounts and sizes of the elements
      \param _targetAmount target amount to satisfy (it is a lower-limit constraint)
      \param _targetAmountPlusOffset target amount plus a positive offset (it is an upper-limit constraint)
      \param _availableTotalSize available total size (in terms of bytes, it is an upper-limit constraint)
      \param _joinsplitsOutputsAmount amounts of joinsplits outputs (order matters)
    */
    CCoinsSelectionForNotes(std::vector<std::pair<CAmount, size_t>> _amountsAndSizes,
                            CAmount _targetAmount,
                            CAmount _targetAmountPlusOffset,
                            size_t _availableTotalSize,
                            std::vector<CAmount> _joinsplitsOutputsAmounts);

    //! Deleted copyconstructor
    CCoinsSelectionForNotes(const CCoinsSelectionForNotes&) = delete;

    //! Deleted move constructor (deletion not needed, but better to be explicit)
    CCoinsSelectionForNotes(CCoinsSelectionForNotes&&) = delete;

    //! Deleted assignment operator
    CCoinsSelectionForNotes& operator=(const CCoinsSelectionForNotes&) = delete;

    //! Deleted move operator (deletion not needed, but better to be explicit)
    CCoinsSelectionForNotes& operator=(CCoinsSelectionForNotes&&) = delete;

    //! Destructor
    ~CCoinsSelectionForNotes();

    //! Method for synchronously running the solving routine with "Sliding Window" strategy
    void Solve() override;
};

/* ---------- CCoinsSelectionForNotes ---------- */

#endif // _COINS_SELECTION_ALGORITHM_H

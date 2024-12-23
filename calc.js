async function calc(number) {
   return new Promise(resolve => {
       setTimeout(() => {
           resolve(number * 100);
       }, 1000);  // 1秒のsleep
   });
}

async function main() {
   console.log("開始時刻:", new Date().toLocaleTimeString());
   const startTime = Date.now();
    const numbers = Array.from({length: 10000}, (_, i) => i + 1);
   const results = await Promise.all(numbers.map(num => calc(num)));

   const total = results.reduce((sum, curr) => sum + curr, 0);
    const endTime = Date.now();
   console.log("終了時刻:", new Date().toLocaleTimeString());
   console.log(`処理時間: ${(endTime - startTime) / 1000}秒`);
   console.log("合計値:", total);
}

main();
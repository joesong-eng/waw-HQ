<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('agent_hardware_products', function (Blueprint $col) {
            $col->id();
            $col->string('hardware_type')->unique(); // e.g., comm_card, kiosk_bridge
            $col->decimal('current_system_cost', 10, 2);
            $col->string('description')->nullable();
            $col->timestamps();
        });

        // Seed initial data
        DB::table('agent_hardware_products')->insert([
            ['hardware_type' => 'comm_card', 'current_system_cost' => 3800.00, 'description' => '標準通訊卡'],
            ['hardware_type' => 'kiosk_bridge', 'current_system_cost' => 30000.00, 'description' => 'Kiosk 轉接卡'],
        ]);
    }

    public function down(): void
    {
        Schema::dropIfExists('agent_hardware_products');
    }
};

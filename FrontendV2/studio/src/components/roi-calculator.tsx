'use client';

import React, { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Separator } from '@/components/ui/separator';
import { Users, Briefcase, IndianRupee, Clock, TrendingUp, BarChart, Percent } from 'lucide-react';

const formatIndianCurrency = (value: number) => {
    if (value >= 10000000) {
        return `₹${(value / 10000000).toFixed(2)} Cr`;
    }
    if (value >= 100000) {
        return `₹${(value / 100000).toFixed(1)} L`;
    }
    return `₹${value.toLocaleString('en-IN')}`;
};

export function RoiCalculator() {
    const [employees, setEmployees] = useState(100);
    const [hiring, setHiring] = useState(10);
    const [salary, setSalary] = useState(6.5); // in Lakhs

    const {
        traditionalCost,
        aiCost,
        annualSavings,
        costReduction,
        breakEvenMonths,
        timeSaved,
        qualityIncrease,
    } = useMemo(() => {
        // Constants based on your system's value proposition
        const avgResumesPerHire = 50; 
        const hrTimePerResume = 0.25; // hours (15 mins)
        const screeningCostPerResume = 20; // INR
        const aiCostPerResume = 2; // INR (90% reduction)
        const aiTimeSavingsPerResume = 0.23; // hours (95% reduction of 15 mins)
        
        const totalHiresPerYear = hiring * 12;
        const totalResumesPerYear = totalHiresPerYear * avgResumesPerHire;
        
        // Traditional Cost Calculation
        const traditionalScreeningCost = totalResumesPerYear * screeningCostPerResume;
        const hrSalaryCostPerYear = (employees / 100) * salary * 100000; // Assuming 1 HR per 100 employees
        const traditionalCost = traditionalScreeningCost + hrSalaryCostPerYear;

        // AI-Powered Cost Calculation
        const aiScreeningCost = totalResumesPerYear * aiCostPerResume;
        // Assuming AI reduces need for HR for screening tasks, let's model a 25% reduction in that portion of HR salary.
        // A more complex model could be used, but this is a reasonable starting point.
        const hrSalaryWithAI = hrSalaryCostPerYear * 0.75; 
        const aiCost = aiScreeningCost + hrSalaryWithAI;

        const annualSavings = traditionalCost - aiCost;
        const costReduction = annualSavings > 0 && traditionalCost > 0 ? (annualSavings / traditionalCost) * 100 : 0;
        const breakEvenMonths = annualSavings > 0 ? (aiCost / (annualSavings / 12)) : 0;

        const timeSaved = (totalResumesPerYear * aiTimeSavingsPerResume); // Total hours saved per year
        const qualityIncrease = 60; // as per your landing page static value

        return {
            traditionalCost,
            aiCost,
            annualSavings,
            costReduction,
            breakEvenMonths: breakEvenMonths > 0 ? breakEvenMonths : 12,
            timeSaved,
            qualityIncrease,
        };
    }, [employees, hiring, salary]);

    return (
        <Card className="mt-12 max-w-4xl mx-auto text-left shadow-2xl">
            <CardHeader>
                <CardTitle className="text-2xl">ROI Calculator</CardTitle>
                <CardDescription>See how much your company can save with AI-powered hiring.</CardDescription>
            </CardHeader>
            <CardContent>
                <div className="grid md:grid-cols-2 gap-8">
                    <div className="space-y-8">
                        <div>
                            <div className="flex justify-between items-center mb-2">
                                <Label htmlFor="employees-slider" className="flex items-center gap-2"><Users /> Company Size</Label>
                                <span className="font-bold text-primary">{employees.toLocaleString('en-IN')}+ employees</span>
                            </div>
                            <Slider id="employees-slider" min={10} max={2000} step={10} value={[employees]} onValueChange={(val) => setEmployees(val[0])} />
                            <div className="flex justify-between text-xs text-muted-foreground mt-1">
                                <span>10</span>
                                <span>1000</span>
                                <span>2000+</span>
                            </div>
                        </div>
                        <div>
                             <div className="flex justify-between items-center mb-2">
                                <Label htmlFor="hiring-slider" className="flex items-center gap-2"><Briefcase /> Monthly Hiring</Label>
                                <span className="font-bold text-primary">{hiring}+ positions</span>
                            </div>
                            <Slider id="hiring-slider" min={1} max={100} step={1} value={[hiring]} onValueChange={(val) => setHiring(val[0])} />
                             <div className="flex justify-between text-xs text-muted-foreground mt-1">
                                <span>1</span>
                                <span>50</span>
                                <span>100+</span>
                            </div>
                        </div>
                        <div>
                            <div className="flex justify-between items-center mb-2">
                                <Label htmlFor="salary-slider" className="flex items-center gap-2"><IndianRupee /> Avg HR Salary</Label>
                                <span className="font-bold text-primary">₹{salary.toFixed(1)} L/year</span>
                            </div>
                            <Slider id="salary-slider" min={3} max={20} step={0.5} value={[salary]} onValueChange={(val) => setSalary(val[0])} />
                             <div className="flex justify-between text-xs text-muted-foreground mt-1">
                                <span>₹3L</span>
                                <span>₹10L</span>
                                <span>₹20L+</span>
                            </div>
                        </div>
                    </div>
                    <div className="bg-muted p-6 rounded-lg space-y-4">
                        <div>
                            <p className="text-sm text-muted-foreground">Traditional Hiring Cost / year</p>
                            <p className="text-2xl font-bold text-destructive line-through">{formatIndianCurrency(traditionalCost)}</p>
                        </div>
                         <div>
                            <p className="text-sm text-muted-foreground">With AI Cost / year</p>
                            <p className="text-2xl font-bold text-green-500">{formatIndianCurrency(aiCost)}</p>
                        </div>
                        <Separator />
                         <div className="bg-primary/10 p-4 rounded-lg">
                            <p className="text-sm text-primary">Annual Savings</p>
                            <p className="text-4xl font-extrabold text-primary">{formatIndianCurrency(annualSavings)}</p>
                            <p className="text-xs text-primary/80 font-medium">{costReduction.toFixed(0)}% cost reduction • Break-even in {breakEvenMonths.toFixed(0)} months</p>
                        </div>
                        <div className="grid grid-cols-2 gap-4 text-center pt-2">
                            <div className="bg-background p-3 rounded-md">
                                <Clock className="h-6 w-6 mx-auto text-secondary"/>
                                <p className="text-lg font-bold">{(timeSaved/12).toFixed(0)}h/mo</p>
                                <p className="text-xs text-muted-foreground">Time Saved</p>
                            </div>
                            <div className="bg-background p-3 rounded-md">
                                <TrendingUp className="h-6 w-6 mx-auto text-secondary"/>
                                <p className="text-lg font-bold">+{qualityIncrease}%</p>
                                <p className="text-xs text-muted-foreground">Hire Quality</p>
                            </div>
                        </div>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
